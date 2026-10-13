"""Send to wiki: bring the team's LLM wiki (a local clone of ael-llm-wiki) up to date with one research run.

Writes what the panel already knows, following the wiki's own rules (its AGENTS.md):
  wiki/runs/run-NNN.md          the run: inputs, AI suggestions, researcher decisions, outputs, activity log
  raw/<folder>/<slug>.md        the source text, word for word (only for a new source; never overwritten)
  wiki/sources/<date>-<slug>.md the source page from the approved evidence (only for a new, accepted source)
  wiki/handbook/<slug>.md       the handbook page, once the final review approved it
  wiki/index.md, wiki/log.md    one line per page in the index, one ingest entry at the top of the log
Then it runs the wiki's tools/lint.py. If the new files add a lint error, everything is put back.
Optionally it pulls first, then commits the files with git and pushes them.

Entity and concept pages are not written here: they need judgement across sources, so they stay
the ingest step the team does with the AI assistant in the wiki repository.
Only published, public material can be sent (rule 2 of the wiki).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
from datetime import date
from pathlib import Path

from agent.text import AgentError

RAW_FOLDER = {"article": "articles", "report": "reports", "other": "other"}


class WikiSettings:
    """Where the wiki clone is on this computer (one setting for the whole panel, in local_settings/)."""

    def __init__(self, folder: Path):
        self.file = Path(folder) / "wiki.json"
        self.lock = threading.Lock()

    def get(self) -> dict:
        try:
            s = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            s = {}
        return {"folder": s.get("folder") or "", "push": bool(s.get("push", True))}

    def set(self, folder: str | None = None, push: bool | None = None) -> dict:
        with self.lock:
            s = self.get()
            if folder is not None:
                s["folder"] = folder.strip().strip('"')
            if push is not None:
                s["push"] = bool(push)
            self.file.parent.mkdir(parents=True, exist_ok=True)
            ignore = self.file.parent / ".gitignore"
            if not ignore.exists():
                ignore.write_text("# Local API keys: never commit.\n*\n", encoding="utf-8")
            self.file.write_text(json.dumps(s, indent=2), encoding="utf-8")
        return s


def wiki_root(folder: str) -> Path:
    if not (folder or "").strip():
        raise AgentError("Enter the folder of your copy of the wiki (the ael-llm-wiki folder on this computer).")
    root = Path(folder.strip().strip('"')).expanduser()
    if not (root / "wiki" / "index.md").exists() or not (root / "wiki" / "log.md").exists() or not (root / "raw").is_dir():
        raise AgentError(f"{root} does not look like the LLM wiki: it needs raw/, wiki/index.md and wiki/log.md.")
    return root


def slugify(text: str, n: int = 70) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    words = re.sub(r"[^a-z0-9]+", " ", text).split()
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > n:
            break
        out = f"{out}-{w}" if out else w
    return out or "source"


def first_name(who: str) -> str:
    return (who or "").split()[0] if (who or "").split() else "unknown"


def _plain(text: str | None) -> str:
    """AI-written English goes on the page without double quotes: the wiki's lint treats any text in
    double quotes as a verbatim quote that must be in the raw file."""
    return re.sub(r"\s+", " ", (text or "").replace('"', "'").replace("“", "'").replace("”", "'")).strip()


def _yaml(text: str | None) -> str:
    return json.dumps(text or "", ensure_ascii=False)


def _normalise(text: str) -> str:  # same as the wiki's tools/lint.py
    text = text.lower().replace("’", "'").replace("‘", "'")
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def _quote_ok(quote: str, raw: str) -> bool:
    hay = _normalise(raw)
    parts = [p for p in re.split(r"\.\.\.|…|\[[^\]]*\]", quote) if len(_normalise(p).split()) >= 1]
    return all(_normalise(p) in hay for p in parts)


def check_sendable(run: dict) -> None:
    """Refuse anything that may never enter the wiki (rule 2 of its AGENTS.md)."""
    src, privacy = run["source"], run["privacy"].get("result")
    if src.get("material") != "published" or src.get("privacy") == "confidential" or privacy not in ("clear", "allowed"):
        raise AgentError("Only published, public sources go to the wiki. Research notes, interview material and "
                         "confidential information never enter it.")


def approved_for_source_page(run: dict) -> list[dict]:
    """A source page needs an accepted appraisal and approved evidence; otherwise only the run page is written."""
    human = (run.get("appraisal") or {}).get("human") or {}
    if human.get("decision") != "accepted" or not run.get("evidence_review"):
        return []
    return [e for e in run.get("evidence") or [] if e.get("approved")]


def run_page_slug(run_id: str) -> str:
    return run_id.lower()


def _status_text(run: dict) -> str:
    human = (run.get("appraisal") or {}).get("human") or {}
    review = run.get("review") or {}
    if run["privacy"].get("result") == "blocked":
        return "Stopped by the privacy check"
    if review:
        return f"Page {'approved' if review.get('decision') == 'approved' else 'sent back for changes'} by {review.get('by')}"
    if run.get("draft"):
        return "Draft written, waiting for the final review"
    if run.get("evidence_review"):
        n = sum(1 for e in run.get("evidence") or [] if e.get("approved"))
        return f"Evidence reviewed by {run['evidence_review'].get('by')} ({n} approved), no draft yet"
    if human:
        return f"Appraisal {human.get('decision')} by {human.get('by')} ({human.get('total')}/10, Tier {human.get('tier')})"
    if (run.get("appraisal") or {}).get("ai"):
        return "AI appraisal suggested, waiting for a researcher"
    if (run.get("translation") or {}).get("paragraphs"):
        return "Translated, not yet appraised"
    return "Ingested, not yet appraised"


def _bullets(items) -> list[str]:
    return [f"- {_plain(x)}" for x in items or [] if _plain(x)]


def _evidence_quote(e: dict) -> list[str]:
    if e.get("problems"):  # not verified by the agent: shown without quotation, so the wiki check does not treat it as a quote
        return [f"  - Proposed quote, NOT found word for word by the agent's check ({'; '.join(_plain(p) for p in e['problems'])}): {_plain(e.get('quote'))}"]
    out = [f"  > {' '.join((e.get('quote') or '').split())}"]
    if e.get("quote_en"):
        out.append(f"  - *English working translation:* {_plain(e['quote_en'])}")
    return out


def _run_page(run: dict, who: str, today: str, source_page: str | None, handbook_page: str | None) -> str:
    src = run["source"]
    tr = run.get("translation") or {}
    appraisal = run.get("appraisal") or {}
    ai, human = appraisal.get("ai") or {}, appraisal.get("human") or {}
    review, check, draft = run.get("review") or {}, run.get("check") or {}, run.get("draft") or {}
    started = (run.get("created") or "")[:10] or "unknown"
    lines = ["---", "type: run", f"run_id: {run['id']}", f"source_title: {_yaml(src.get('title'))}",
             f"started: {started}", f"status: {_yaml(_status_text(run))}", f"started_by: {_yaml(run.get('started_by') or '')}",
             f"sent_by: {_yaml(who)}", f"date_sent: {today}", "---", "",
             f"# {run['id']}: {_plain(tr.get('title') or src.get('title'))}", "",
             f"The record of research run {run['id']} in the research agent (agent v0), sent from its panel. "
             "Text written by the AI (reasons, claims, translations, the draft) is a suggestion or working text, not evidence. "
             "The evidence is the source text in raw/ and the verbatim quotes.", "",
             "## Input", "",
             f"- **Title:** {_plain(src.get('title'))}" + (f" (English: {_plain(tr['title'])})" if tr.get("title") and tr["title"] != src.get("title") else ""),
             f"- **Organisation:** {_plain(src.get('organisation') or 'not recorded')}",
             f"- **Published:** {src.get('date') or 'not recorded'}",
             f"- **Link or file:** {src.get('url') or src.get('file') or 'pasted text'}",
             f"- **Language:** {src.get('language') or 'not recorded'}; material: {src.get('material')}; privacy status: {src.get('privacy')}",
             f"- **Retrieved:** {src.get('retrieved') or 'not recorded'}; {len(run.get('paragraphs') or [])} paragraphs (P1, P2 …)",
             f"- **Capture:** {_plain(src.get('capture') or 'not recorded')}",
             f"- **Handbook question:** {_plain(run.get('question'))}",
             f"- **Privacy check:** {run['privacy'].get('result')}. {_plain(run['privacy'].get('reason'))}"
             + (f" Decided by {run['privacy']['decided_by']}: {_plain(run['privacy'].get('note'))}" if run["privacy"].get("decided_by") else ""),
             f"- **Source page in this wiki:** [[{source_page}]]" if source_page else "- **Source page in this wiki:** none yet",
             "", "## Translation", ""]
    if not tr.get("needed"):
        lines.append("Not needed.")
    elif not tr.get("paragraphs"):
        lines.append("Needed, not done yet.")
    else:
        lines.append(f"English working translation of {len(tr['paragraphs'])} paragraphs by the AI. Terms the AI was unsure about:")
        lines += [f"- {t.get('paragraph')}: {_plain(t.get('term'))} → {_plain(t.get('used'))}. {_plain(t.get('why'))}"
                  for t in tr.get("uncertain_terms") or []]
        lines += _bullets(tr.get("notes") if isinstance(tr.get("notes"), list) else [tr.get("notes")])
    lines += ["", "## Appraisal", ""]
    if not ai:
        lines.append("Not appraised yet.")
    else:
        scores = ai.get("scores") or {}
        lines += ["Rubric v1.0. The AI suggests, the researcher decides; only the researcher's scores count.", "",
                  "| Criterion | AI | Researcher | AI's reason (summary by the AI) |", "|---|---|---|---|"]
        for k, v in scores.items():
            mine = (human.get("scores") or {}).get(k, "–")
            reason = _plain(v.get("reason")).replace("|", "/")
            lines.append(f"| {k} | {v.get('score')} | {mine} | {reason} |")
        lines += ["", f"- **AI suggestion:** {ai.get('total')}/10, Tier {ai.get('tier')}"]
        if human:
            lines.append(f"- **Researcher's decision:** {human.get('decision')}, {human.get('total')}/10, Tier {human.get('tier')}, by "
                         f"{human.get('by')} on {(human.get('at') or '')[:10]}"
                         + (f"; changed {', '.join(human['changed'])}" if human.get("changed") else "; AI scores accepted unchanged")
                         + (f"; note: {_plain(human['note'])}" if human.get("note") else ""))
        else:
            lines.append("- **Researcher's decision:** not made yet")
        checks = ai.get("checks") or {}
        if checks:
            lines += ["", "AI checks:"] + [f"- **{k}:** {_plain(v)}" for k, v in checks.items()]
        if ai.get("limitations"):
            lines += ["", "Limitations named by the AI:"] + _bullets(ai["limitations"])
        if ai.get("questions"):
            lines += ["", "Open questions from the AI:"] + _bullets(ai["questions"])
    lines += ["", "## Evidence", ""]
    evidence = run.get("evidence") or []
    if not evidence:
        lines.append("No evidence proposed yet.")
    else:
        rev = run.get("evidence_review") or {}
        lines.append(f"{len(evidence)} items proposed by the AI and checked by the agent; "
                     + (f"{sum(1 for e in evidence if e.get('approved'))} approved by {rev.get('by')} on {(rev.get('at') or '')[:10]}."
                        if rev else "not reviewed yet."))
        lines.append("")
        for e in evidence:
            mark = "approved" if e.get("approved") else ("not approved" if rev else "not reviewed")
            lines.append(f"- **{e['id']}** ({mark}; {e.get('type') or 'claim'}; {e.get('paragraph') or 'no paragraph'}): {_plain(e.get('claim'))}"
                         + (f" Limitation: {_plain(e['limitation'])}" if e.get("limitation") else ""))
            lines += _evidence_quote(e)
    lines += ["", "## Draft and check", ""]
    if not draft:
        lines.append("No draft yet.")
    else:
        lines.append(f"Draft: *{_plain(draft.get('title'))}*" + (f", see [[{handbook_page}]]." if handbook_page else " (not approved, so not in the handbook)."))
        if check:
            lines += ["", f"Automated check: {check.get('errors')} errors, {check.get('warnings')} warnings."]
            lines += [f"- {_plain(i.get('group'))} ({i.get('level')}): {_plain(i.get('text'))}" for i in check.get("items") or []
                      if not (i.get("text") or "").startswith("From the draft:")]  # those repeat the notes below
        if draft.get("notes_for_reviewer"):
            lines += ["", "Notes from the AI for the reviewer:"] + _bullets(draft["notes_for_reviewer"])
    lines += ["", "## Review", ""]
    lines.append(f"{review.get('decision')} by {review.get('by')} on {(review.get('at') or '')[:10]}"
                 + (f". Note: {_plain(review['note'])}" if review.get("note") else "") if review else "Not reviewed yet.")
    lines += ["", "## Activity log", ""]
    lines += [f"- {l.get('time', '').replace('T', ' ')} · {_plain(l.get('who'))} · {_plain(l.get('what'))}" for l in run.get("log") or []
              if not (l.get("what") or "").startswith("sent to the LLM wiki")]  # sending is recorded in the wiki's own log
    if run.get("history"):
        lines.append(f"- Earlier versions of reopened steps are kept in the run file ({len(run['history'])} entries).")
    links = [f"[[{x}]]" for x in (source_page, handbook_page) if x]
    lines += ["", "## Links", "", " · ".join(links) if links else "No source or handbook page in the wiki yet."]
    return "\n".join(lines) + "\n"


KIND_LABEL = {"evidence": "Evidence", "interpretation": "Interpretation", "assumption": "Assumption",
              "recommendation": "Recommendation", "example": "Example"}


def handbook_slug(run: dict) -> str:
    return slugify(run["draft"].get("title") or run["id"])


def _handbook_page(run: dict, source_page: str | None) -> str:
    d, review, src = run["draft"], run["review"], run["source"]
    ev = {e["id"]: e for e in run.get("evidence") or []}
    lines = ["---", "type: handbook", f"run_id: {run['id']}", f"question: {_yaml(_plain(run.get('question')))}",
             f"approved_by: {_yaml(review.get('by'))}", f"date_approved: {(review.get('at') or '')[:10]}",
             f"source: {_yaml(src.get('title'))}", "---", "",
             f"# {_plain(d.get('title'))}", "",
             f"*Handbook page drafted by the research agent from the approved evidence of one source, and approved by "
             f"{review.get('by')} on {(review.get('at') or '')[:10]}"
             + (f" (note: {_plain(review['note'])})" if review.get("note") else "") + ". Citations such as [E1] are the "
             f"evidence items of [[{run_page_slug(run['id'])}]]; their quotes are listed at the end.*", "",
             f"**Question:** {_plain(run.get('question'))}", ""]
    cited = []
    for section in d.get("sections") or []:
        lines += [f"## {_plain(section.get('heading'))}", ""]
        for b in section.get("blocks") or []:
            cites = b.get("evidence") or []
            cited += [c for c in cites if c not in cited]
            label = KIND_LABEL.get(b.get("kind"), b.get("kind") or "")
            if b.get("kind") == "example" and not cites:
                label += " (hypothetical)"
            lines += [f"**{label}:** {_plain(b.get('text'))}" + (f" [{', '.join(cites)}]" if cites else ""), ""]
    if d.get("decision_questions"):
        lines += ["## Questions for your agency", ""] + _bullets(d["decision_questions"]) + [""]
    lines += ["## Quotes", "", "The quotes behind the citations, word for word from the source."
              + (" The English lines are a working translation, not evidence." if src.get("language") == "nl" else ""), ""]
    for cid in cited:
        e = ev.get(cid)
        if not e or e.get("problems"):
            continue
        lines += [f"**[{cid}]** {_plain(e.get('claim'))} ({e.get('paragraph')})", "", f"> {' '.join(e['quote'].split())}", ""]
        if e.get("quote_en"):
            lines += [f"*{_plain(e['quote_en'])}*", ""]
    links = [f"[[{run_page_slug(run['id'])}]]"] + ([f"[[{source_page}]]"] if source_page else [])
    lines += ["## Links", "", " · ".join(links)]
    return "\n".join(lines) + "\n"


SECTION_INTRO = {"Sources": None, "Agent runs": "Sent from the research agent's panel; one page per research run.",
                 "Handbook pages": "Pages approved in the research agent's final review; one source each."}


def _upsert_index(text: str, section: str, page: str, line_text: str, first: bool = True) -> str:
    """Put one line for a page in a section of the index, replacing an earlier line for the same page."""
    entry = f"- [[{page}]]: {line_text}"
    pattern = re.compile(rf"^- \[\[{re.escape(page)}\]\].*$", re.M)
    if pattern.search(text):
        return pattern.sub(lambda _: entry, text, count=1)
    m = re.search(rf"^## {re.escape(section)}\s*\n", text, re.M)
    if not m:
        intro = f"{SECTION_INTRO.get(section)}\n\n" if SECTION_INTRO.get(section) else ""
        return text.rstrip("\n") + f"\n\n## {section}\n\n{intro}{entry}\n"
    start = m.end()
    nxt = re.search(r"^## ", text[start:], re.M)
    end = start + nxt.start() if nxt else len(text)
    body = text[start:end]
    items = [i for i, l in enumerate(body.split("\n")) if l.startswith("- [[")]
    rows = body.split("\n")
    if not items:
        rows = [r for r in rows]
        insert_at = len(rows) - 1 if rows and rows[-1] == "" else len(rows)
        while insert_at > 0 and rows[insert_at - 1] == "":
            insert_at -= 1
        rows[insert_at:insert_at] = ([""] if insert_at else []) + [entry]
    else:
        rows.insert(items[0] if first else items[-1] + 1, entry)
    return text[:start] + "\n".join(rows) + text[end:]


def _add_link_to_source_page(text: str, link: str) -> str:
    """Add a wikilink to the Links section of an existing source page (nothing else on the page changes)."""
    if f"[[{link}]]" in text:
        return text
    m = re.search(r"^## Links\s*\n", text, re.M)
    if not m:
        return text.rstrip("\n") + f"\n\n## Links\n\n[[{link}]]\n"
    rest = text[m.end():]
    first = re.search(r"^\[\[.*$", rest, re.M)
    if first and not re.search(r"^## ", rest[:first.start()], re.M):
        line = first.group(0).rstrip()
        return text[:m.end()] + rest[:first.start()] + f"{line} · [[{link}]]" + rest[first.end():]
    return text[:m.end()] + f"\n[[{link}]]\n" + rest


def _existing_page(root: Path, run: dict, page: str) -> str | None:
    """The source page this run's source already has in the wiki: same file name, same link or file, a page that
    names this run, or the same title."""
    src = run["source"]
    url = (src.get("url") or "").strip().rstrip("/")
    file = (src.get("file") or "").strip()
    title = slugify(re.sub(r"\((en|nl)\)\s*$", "", src.get("title") or "", flags=re.I), 200)
    by_run = by_title = None
    for p in sorted((root / "wiki" / "sources").glob("*.md")):
        if p.stem == page:
            return p.stem
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'^url:\s*"?([^"\n]+)"?\s*$', text[:2000], re.M)
        page_url = m.group(1).strip().rstrip("/") if m else ""
        if (url and page_url == url) or (file and file in page_url):
            return p.stem
        if re.search(rf"\b{re.escape(run['id'])}\b", text):
            by_run = by_run or p.stem
        t = re.search(r'^title:\s*"?([^"\n]+)"?\s*$', text[:2000], re.M)
        if title and t and slugify(t.group(1), 200).startswith(title):
            by_title = by_title or p.stem
    return by_run or by_title


def _kind(src: dict) -> str:
    if src.get("url"):
        return "report" if src["url"].lower().split("?")[0].endswith(".pdf") else "article"
    return "report" if (src.get("file") or "").lower().endswith(".pdf") else "other"


def _raw_text(ws_root: Path, run: dict, approved: list[dict]) -> str:
    """The source text as the agent read it. original.txt when every approved quote is in it, else the paragraphs
    (which are what the agent checked the quotes against)."""
    original = ws_root / run["id"] / "original.txt"
    paras = "\n\n".join(p["text"] for p in run.get("paragraphs") or [])
    if original.exists():
        text = original.read_text(encoding="utf-8", errors="replace")
        if all(_quote_ok(e["quote"], text) for e in approved):
            return text
    if not paras:
        raise AgentError("The source text of this run is not available any more, so it cannot be filed in the wiki.")
    return paras


def _source_page(run: dict, approved: list[dict], who: str, today: str, raw_rel: str, kind: str, page: str,
                 org_page: str | None) -> str:
    src, human, ai = run["source"], run["appraisal"]["human"], run["appraisal"].get("ai") or {}
    title = src.get("title") or "Untitled"
    en_title = (run.get("translation") or {}).get("title")
    dutch = src.get("language") == "nl"
    org = src.get("organisation") or "organisation not recorded"
    year = (src.get("date") or "")[:4] or "undated"
    paragraphs = {p["id"] for p in run.get("paragraphs") or []}
    rubric_note = f"; note: {_plain(human['note'])}" if human.get("note") else ""
    length = f"{len(paragraphs)} paragraphs (read in full by agent v0, run {run['id']})"
    changed = f", researcher changed {', '.join(human['changed'])}" if human.get("changed") else ", AI suggestion accepted unchanged"

    lines = ["---", "type: source", f"kind: {kind}", f"title: {_yaml(title)}", f"author: [{_yaml(org)}]",
             f"publisher: {_yaml(org)}", f"url: {_yaml(src.get('url') or 'none (file: ' + (src.get('file') or 'pasted text') + ')')}",
             f"date_published: {src.get('date') or 'unknown'}", f"date_ingested: {today}",
             f"added_by: {_yaml(first_name(who))}", f"raw: {_yaml('../../' + raw_rel)}",
             f"length: {_yaml(length)}",
             "---", "", f"# {_plain(title)} ({_plain(org)}, {year})", ""]
    if en_title and en_title != title:
        lines += [f"*English title (working translation): {_plain(en_title)}.* The source is in Dutch. Quotes below are the "
                  "Dutch original; the English lines in italics are the agent's working translation and are not evidence.", ""]
    lines += ["## TL;DR", ""]
    lines += [f"- {_plain(e['claim'])} ({e.get('paragraph') or 'location not recorded'})" for e in approved[:6]]
    lines += ["", "## Key claims", ""]
    for e in approved:
        lim = f" Limitation: {_plain(e['limitation'])}" if e.get("limitation") else ""
        lines.append(f"- {_plain(e['claim'])} Paragraph {e.get('paragraph') or 'not recorded'} of the raw file "
                     f"(evidence {run['id']}-{e['id']}, {e.get('type') or 'claim'}).{lim}")
    lines += ["", "## Quotes", ""]
    for e in approved:
        quote = " ".join(e["quote"].split())
        lines += [f"> {quote}", ""]
        if dutch and e.get("quote_en"):
            lines += [f"*{_plain(e['quote_en'])}*", ""]
    lines += ["## Caveats", "",
              f"- **Who published it:** {_plain(org)}. Recorded by the researcher in the panel; check during the full ingest.",
              f"- **Team appraisal (rubric v1.0, agent v0):** {human['total']}/10, Tier {human['tier']}, {human['decision']} by "
              f"{human['by']} (run {run['id']}, {human['at'][:10]}{changed}{rubric_note})."]
    lines += [f"- {_plain(x)}" for x in ai.get("limitations") or []]
    if src.get("capture"):
        lines.append(f"- **Capture:** {_plain(src['capture'])}")
    if dutch:
        lines.append("- **Language:** Dutch. The English lines are a working translation by the AI, not evidence.")
    lines += ["- **Not yet checked by the wiki ingest:** text aimed at an AI, links to entity and concept pages, and "
              "contradictions with other sources. Ask the assistant in the wiki repository to finish the ingest.",
              "", "## Links", ""]
    links = ([f"[[{org_page}]]"] if org_page else []) + [f"[[{run_page_slug(run['id'])}]]"]
    lines.append(" · ".join(links))
    if not org_page:
        lines += ["", "No entity or concept pages yet: they are added when the team finishes the ingest with the assistant."]
    return "\n".join(lines) + "\n"


def _insert_log(text: str, entry: str) -> str:
    """New entries go at the top, directly under the --- line."""
    idx = text.find("\n---\n")
    if idx < 0:
        return text.rstrip("\n") + "\n\n---\n\n" + entry.rstrip("\n") + "\n"
    rest = text[idx + 5:].lstrip("\n")
    return text[:idx + 5] + "\n" + entry.rstrip("\n") + "\n\n" + rest


def _lint(root: Path) -> tuple[set[str], str]:
    tool = root / "tools" / "lint.py"
    if not tool.exists():
        return set(), "no tools/lint.py in this wiki"
    p = subprocess.run([sys.executable, str(tool)], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    errors = {line for line in out.splitlines() if line.startswith("ERROR")}
    summary = next((line.strip() for line in reversed(out.splitlines()) if "error(s)" in line), out.strip()[-200:])
    return errors, summary


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _same(old: str | None, new: str) -> bool:
    """Equal apart from who sent the page and when."""
    strip = lambda t: re.sub(r"^(sent_by|date_sent):.*$", "", t or "", flags=re.M)
    return old is not None and strip(old) == strip(new)


def _find_handbook_page(root: Path, run_id: str) -> str | None:
    for p in (root / "wiki" / "handbook").glob("*.md"):
        if re.search(rf"^run_id:\s*{re.escape(run_id)}\s*$", p.read_text(encoding="utf-8", errors="ignore")[:1000], re.M):
            return p.stem
    return None


def _org_page(root: Path, org: str | None) -> str | None:
    if not org:
        return None
    for cand in (slugify(org), slugify(re.sub(r"\(.*?\)", "", org))):
        if (root / "wiki" / "entities" / f"{cand}.md").exists():
            return cand
    m = re.search(r"\(([A-Za-z]{2,10})\)", org)
    if m and (root / "wiki" / "entities" / f"{m[1].lower()}.md").exists():
        return m[1].lower()
    return None


def send(ws_root: Path, run: dict, who: str, folder: str, push: bool = True, today: str | None = None) -> dict:
    """Bring the wiki up to date with one run. Always writes the run page. Adds the raw file and source page when
    the source is accepted, has approved evidence and is not in the wiki yet, and the handbook page when the final
    review approved it. Returns what was done; the caller stores it in the run and saves it."""
    check_sendable(run)
    root = wiki_root(folder)
    src = run["source"]
    today = today or date.today().isoformat()
    has_git = bool(shutil.which("git")) and (root / ".git").exists()
    pulled = ""
    if has_git and push:  # start from the team's latest version, so the push afterwards is not refused
        p = _git(root, "pull", "--ff-only")
        pulled = "" if p.returncode == 0 else "Could not update the wiki folder from GitHub first (git pull): " + (p.stderr or p.stdout).strip()[-200:]

    approved = approved_for_source_page(run)
    slug = slugify(src.get("title") or run["id"])
    page = f"{src.get('date') or 'undated'}-{slug}"
    source_page = _existing_page(root, run, page)
    new_source = not source_page and bool(approved)
    org_page = _org_page(root, src.get("organisation"))
    run_slug = run_page_slug(run["id"])
    approved_page = (run.get("review") or {}).get("decision") == "approved" and run.get("draft")
    hb_slug = None
    if approved_page:
        hb_slug = _find_handbook_page(root, run["id"]) or handbook_slug(run)
        other = root / "wiki" / "handbook" / f"{hb_slug}.md"
        if other.exists() and f"run_id: {run['id']}" not in other.read_text(encoding="utf-8", errors="ignore"):
            hb_slug = f"{hb_slug}-{run_slug}"

    writes: dict[Path, str] = {}
    new_files, updated = [], []
    if new_source:
        kind = _kind(src)
        raw_path = root / "raw" / RAW_FOLDER[kind] / f"{slug}.md"
        if raw_path.exists():
            raise AgentError(f"raw/{RAW_FOLDER[kind]}/{raw_path.name} already exists, and raw files are never overwritten.")
        raw_rel = f"raw/{RAW_FOLDER[kind]}/{raw_path.name}"
        capture = (f"Read by the research agent (agent v0, run {run['id']}) on {src.get('retrieved') or 'an unknown date'}. "
                   + (src.get("capture") or "") + f" Sent to the wiki from the panel by {who} on {today}.")
        writes[raw_path] = "\n".join(["---", f"title: {_yaml(src.get('title'))}", f"url: {_yaml(src.get('url') or '')}",
                                      f"author: {_yaml(src.get('organisation') or '')}", f"date_published: {src.get('date') or 'unknown'}",
                                      f"retrieved: {src.get('retrieved') or 'unknown'}", f"language: {src.get('language') or 'unknown'}",
                                      f"capture: {_yaml(capture)}", "---", "", _raw_text(ws_root, run, approved).strip(), ""])
        source_page = page
        writes[root / "wiki" / "sources" / f"{page}.md"] = _source_page(run, approved, who, today, raw_rel, kind, page, org_page)
        new_files += [raw_rel, f"[[{page}]]"]
    elif source_page:
        sp = root / "wiki" / "sources" / f"{source_page}.md"
        text = sp.read_text(encoding="utf-8")
        changed = _add_link_to_source_page(text, run_slug)
        if changed != text:
            writes[sp] = changed
            updated.append(f"[[{source_page}]] (link to {run['id']})")

    run_path = root / "wiki" / "runs" / f"{run_slug}.md"
    (updated if run_path.exists() else new_files).append(f"[[{run_slug}]]")
    writes[run_path] = _run_page(run, who, today, source_page, hb_slug)
    if hb_slug:
        hb_path = root / "wiki" / "handbook" / f"{hb_slug}.md"
        (updated if hb_path.exists() else new_files).append(f"[[{hb_slug}]]")
        writes[hb_path] = _handbook_page(run, source_page)

    index_file, log_file = root / "wiki" / "index.md", root / "wiki" / "log.md"
    index = index_file.read_text(encoding="utf-8")
    title_line = _plain((run.get("translation") or {}).get("title") or src.get("title"))
    org = _plain(src.get("organisation") or "")
    status = _status_text(run)
    status = status[:1].lower() + status[1:]
    if new_source:
        index = _upsert_index(index, "Sources", page,
                              f"{org or 'Publisher not recorded'}: {title_line} ({(src.get('date') or 'undated')[:4]}; filed from the panel, ingest to finish).")
    index = _upsert_index(index, "Agent runs", run_slug, f"{run['id']}, {title_line}" + (f" ({org})" if org else "") + f": {status}.", first=False)
    if hb_slug:
        index = _upsert_index(index, "Handbook pages", hb_slug,
                              f"{_plain(run['draft'].get('title'))} (from {run['id']}, approved by {run['review'].get('by')}).")
    writes[index_file] = index
    log_before = log_file.read_text(encoding="utf-8")
    entry = "\n".join([f"## [{today}] ingest | {run['id']} from the panel — {_plain(src.get('title'))}", "",
                       f"- Added by: {first_name(who)} (Send to wiki, agent v0 panel)",
                       f"- New: {', '.join(new_files) or 'none'}",
                       f"- Updated: {', '.join(updated) or 'none'}",
                       "- Debates: not checked; the full ingest with the assistant compares new sources with the wiki"
                       if new_source else "- Debates: none (no new source)",
                       "- Lint: {lint}", "", ""])

    before = {path: (path.read_text(encoding="utf-8") if path.exists() else None) for path in list(writes) + [log_file]}
    if all(_same(before[path], text) for path, text in writes.items()):
        raise AgentError("The wiki is already up to date with this run: nothing has changed since it was last sent.")
    errors_before, _ = _lint(root)
    for path, text in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    log_file.write_text(_insert_log(log_before, entry.replace("{lint}", "checking")), encoding="utf-8")
    errors_after, summary = _lint(root)
    new_errors = sorted(errors_after - errors_before)
    if new_errors:  # put everything back: the wiki must stay clean
        for path, text in before.items():
            if text is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(text, encoding="utf-8")
        hint = (" The wiki folder may be out of date: open GitHub Desktop, click Fetch origin and Pull, then try again."
                if any("type is 'run'" in e or "type is 'handbook'" in e for e in new_errors) else "")
        raise AgentError("The wiki check (tools/lint.py) found problems, so nothing was filed: "
                         + "; ".join(e[7:] for e in new_errors[:5]) + hint)
    log_file.write_text(_insert_log(log_before, entry.replace("{lint}", summary)), encoding="utf-8")

    result = {"by": who, "at": today, "run_page": run_slug, "source_page": source_page, "handbook_page": hb_slug,
              "new_source": new_source, "raw": raw_rel if new_source else None, "lint": summary, "commit": None, "pushed": False, "git": pulled}
    files = [str(p.relative_to(root)).replace("\\", "/") for p in writes] + ["wiki/log.md"]
    if has_git:
        add = _git(root, "add", "--", *files)
        msg = (f"{run['id']} from the panel: {src.get('title')}\n\nSent from agent v0 by {who}: run page"
               + (", source page and raw file" if new_source else "") + (", handbook page" if hb_slug else "") + ".")
        commit = _git(root, "commit", "-m", msg, "--", *files) if add.returncode == 0 else add
        if commit.returncode == 0:
            result["commit"] = _git(root, "rev-parse", "--short", "HEAD").stdout.strip()
            if push:
                p = _git(root, "push")
                result["pushed"] = p.returncode == 0
                if p.returncode != 0:
                    result["git"] = "Committed, but the push failed (push it from GitHub Desktop): " + (p.stderr or p.stdout).strip()[-300:]
        elif "nothing to commit" in (commit.stdout + commit.stderr):
            result["git"] = "The wiki already had this version of the run, so there was nothing new to commit."
        else:
            result["git"] = "Files written, but git did not commit them: " + (commit.stderr or commit.stdout).strip()[-300:]
    else:
        result["git"] = "Files written. Git was not found, so commit and push them from GitHub Desktop."
    return result
