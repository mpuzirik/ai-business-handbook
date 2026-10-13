"""AEL Research Agent v0 - the whole workflow for one source ("a research run").

    1 Ingest  2 Privacy check  3 Translate  4 Appraise  5 Extract evidence
    6 Organise  7 Draft  8 Check  9 Human review          (Publish is not part of v0)

A run is one JSON file (workspace/<RUN-ID>/run.json) plus the unchanged source text.
The agent does the tool work itself, writes a prompt for each AI step (the researcher
copies it into Claude and pastes the answer back), checks every answer, and STOPS at
every decision that belongs to a person. The code never decides whether a source is
accepted, whether evidence is used, or whether a page is approved.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from agent import text as T
from agent.rubric import as_prompt_text, load_rubric, tier_for
from agent.text import AgentError

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = Path(__file__).parent / "prompts"

STAGES = ["Ingest", "Privacy check", "Translate", "Appraise", "Extract evidence", "Organise", "Draft", "Check",
          "Human review"]
MATERIAL = {  # what the researcher says the source is
    "published": "Published source (article, report, web page)",
    "own_note": "Own research note",
    "transcript_anonymised": "Anonymised interview transcript (consent process followed)",
    "transcript_identifiable": "Identifiable interview transcript",
    "recording": "Interview recording (audio/video)",
    "confidential": "Confidential company information",
}
RESTRICTED = {"transcript_identifiable", "recording", "confidential"}  # PRD 4 / Blueprint 5: never to an AI service
PRIVACY = {"public": "Public", "approved": "Anonymised and approved", "confidential": "Confidential",
           "unknown": "Not sure"}
DEFAULT_QUESTION = "What does this evidence mean for the owner of a small marketing agency, and what should they do?"
KINDS = {"evidence", "interpretation", "assumption", "recommendation", "example"}
REQUIRED_SECTIONS = {"opportunities": "Opportunities", "limitations": "Limitations",
                     "responsible_ai": "Responsible AI", "actions": "Actions"}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_context() -> dict:
    ctx = json.loads((ROOT / "context" / "project_context.json").read_text(encoding="utf-8"))
    ref = ctx["rubric_reference"]
    path = (ROOT / ref["file"]).resolve()
    if not path.exists():  # in the team repository the search strategy sits next to this folder, not in Context/
        alt = (ROOT / ".." / Path(ref["file"]).name).resolve()
        path = alt if alt.exists() else path
    ctx["rubric"] = load_rubric(path, ref["expected_version"])
    return ctx


def context_text(ctx: dict) -> str:
    lines = [f"Target SME: {ctx['target_sme']['sector']} {ctx['target_sme']['size']} {ctx['target_sme']['region']}",
             f"Business decision the handbook serves: {ctx['business_decision']}", "Research questions:"]
    lines += [f"- {k}: {v}" for k, v in ctx["research_questions"].items()]
    lines.append("Scope rules:")
    lines += [f"- {r}" for r in ctx["scope_rules"]]
    lines.append("Responsible-AI issues: " + ", ".join(ctx["responsible_ai_issues"]["allowed"]))
    return "\n".join(lines)


def check_reviewer(name: str | None) -> str:
    name = (name or "").strip()
    if not name:
        raise AgentError("Type your name in the top bar first. Every decision is recorded with the name of the person who made it.")
    if re.search(r"\b(claude|ai|agent|assistant|gpt|bot)\b", name, re.I):
        raise AgentError("Decisions must be made by a person, not by an AI. Use your own name.")
    return name


# ================================================================ storage

class Workspace:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def ids(self) -> list[str]:
        return sorted(p.parent.name for p in self.root.glob("RUN-*/run.json"))

    def load(self, run_id: str) -> dict:
        path = self.root / run_id / "run.json"
        if not re.fullmatch(r"RUN-\d{3,}", run_id) or not path.exists():
            raise AgentError(f"Unknown research run {run_id}.")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, run: dict) -> dict:
        folder = self.root / run["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        return run

    def new_id(self) -> str:
        # deleted runs count too, so a run number is never used twice
        used = self.ids() + [p.name.split("_")[0] for p in (self.root / "deleted").glob("RUN-*")]
        numbers = [int(i.split("-")[1]) for i in used if re.fullmatch(r"RUN-\d+", i)]
        return f"RUN-{max(numbers, default=0) + 1:03d}"

    def delete(self, run_id: str, who: str) -> None:
        """Move a run to workspace/deleted/ (out of every list; can be restored by moving the folder back)."""
        run = self.load(run_id)
        run["deleted"] = {"by": who, "at": now()}
        self.save(run)
        target = self.root / "deleted" / run_id
        n = 1
        while target.exists():
            n += 1
            target = self.root / "deleted" / f"{run_id}_{n}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self.root / run_id), str(target))

    # ---- recently deleted
    def _deleted_folder(self, folder: str) -> Path:
        path = self.root / "deleted" / folder
        if not re.fullmatch(r"RUN-\d{3,}(_\d+)?", folder) or not (path / "run.json").exists():
            raise AgentError(f"{folder} is not in Recently deleted.")
        return path

    def deleted(self) -> list[dict]:
        """Deleted runs, most recently deleted first."""
        out = []
        for path in (self.root / "deleted").glob("RUN-*/run.json"):
            run = json.loads(path.read_text(encoding="utf-8"))
            d = run.get("deleted") or {}
            out.append({"folder": path.parent.name, "id": run["id"], "title": display_title(run), "owner": owner(run),
                        "started_login": run.get("started_login"),
                        "created": run["created"], "deleted_by": d.get("by"), "deleted_at": d.get("at")})
        return sorted(out, key=lambda x: x["deleted_at"] or "", reverse=True)

    def deleted_run(self, folder: str) -> dict:
        return json.loads((self._deleted_folder(folder) / "run.json").read_text(encoding="utf-8"))

    def restore(self, folder: str, who: str) -> str:
        path = self._deleted_folder(folder)
        run = json.loads((path / "run.json").read_text(encoding="utf-8"))
        if (self.root / run["id"]).exists():
            raise AgentError(f"{run['id']} already exists, so this copy cannot be restored.")
        shutil.move(str(path), str(self.root / run["id"]))
        d = run.pop("deleted", {}) or {}
        log(run, who, f"restored from Recently deleted (deleted by {d.get('by', 'unknown')} on {str(d.get('at', ''))[:10]})")
        self.save(run)
        return run["id"]

    def purge(self, folder: str) -> str:
        """Delete permanently: the files are removed from the computer."""
        path = self._deleted_folder(folder)
        run_id = json.loads((path / "run.json").read_text(encoding="utf-8"))["id"]
        shutil.rmtree(path)
        return run_id


AUTOMATIC = {"agent", "ai (pasted by researcher)"}


def is_automatic(who: str | None) -> bool:
    """True for entries made by the agent or an AI (pasted, or sent through the Claude API), not by a person."""
    return who in AUTOMATIC or (who or "").startswith("ai (")


def may_delete(run: dict, account: dict | None) -> bool:
    """Only the person who started a run may delete, restore or permanently delete it.
    Runs from before accounts existed only have a typed name: that name must match the account's full or first name."""
    if not account:
        return False
    if run.get("started_login"):
        return run["started_login"] == account["login"]
    typed = (owner(run) or "").strip().lower()
    return bool(typed) and typed in {account["name"].lower(), (account.get("first_name") or "").lower()}


def _need_creator(run: dict, account: dict | None) -> None:
    if not may_delete(run, account):
        raise AgentError(f"Only {owner(run) or 'the person who started it'} can delete {run['id']}.")


def delete_run(ws: Workspace, run_id: str, account: dict) -> None:
    run = ws.load(run_id)
    _need_creator(run, account)
    ws.delete(run_id, check_reviewer(account["name"]))


def deleted_for(ws: Workspace, account: dict) -> list[dict]:
    """Recently deleted, limited to the runs this account started (only they can restore or remove them)."""
    return [d for d in ws.deleted() if may_delete(ws.deleted_run(d["folder"]), account)]


def restore_run(ws: Workspace, folder: str, account: dict) -> str:
    _need_creator(ws.deleted_run(folder), account)
    return ws.restore(folder, account["name"])


def purge_run(ws: Workspace, folder: str, account: dict) -> str:
    _need_creator(ws.deleted_run(folder), account)
    return ws.purge(folder)


def stats(ws: Workspace, account: dict) -> dict:
    """Personal statistics for one account, from the saved runs (deleted runs not counted)."""
    me = account["name"].lower()
    mine = lambda who: (who or "").strip().lower() == me  # noqa: E731
    runs = [ws.load(i) for i in ws.ids()]
    started = [r for r in runs if may_delete(r, account)]
    by_state = {"ai": 0, "human": 0, "done": 0, "stopped": 0}
    for r in started:
        by_state[status(r)["who"]] += 1
    contributed = [r for r in runs if r not in started and any(mine(e["who"]) for e in r["log"])]
    waiting = [r for r in started if status(r)["who"] == "human"]

    appraisals = [r["appraisal"]["human"] for r in runs if (r.get("appraisal") or {}).get("human") and mine(r["appraisal"]["human"]["by"])]
    tiers = {t: sum(1 for a in appraisals if a["tier"] == t) for t in ("A", "B", "C")}
    reviewed = [r for r in runs if r.get("evidence_review") and mine(r["evidence_review"]["by"])]
    ev_seen = sum(len(r["evidence"] or []) for r in reviewed)
    ev_ok = sum(1 for r in reviewed for e in (r["evidence"] or []) if e.get("approved"))
    my_log = [e for r in runs for e in r["log"] if mine(e["who"])]
    count = lambda prefix: sum(1 for e in my_log if e["what"].startswith(prefix))  # noqa: E731
    return {
        "name": account["name"], "login": account["login"], "member_since": account.get("created"),
        "last_activity": max((e["time"] for e in my_log), default=None),
        "runs": {"started": len(started), "contributed": len(contributed), "waiting_for_you": len(waiting), **by_state},
        "decisions": {
            "total": len(my_log),
            "privacy": count("privacy decision"),
            "appraisals": len(appraisals),
            "accepted": sum(1 for a in appraisals if a["decision"] == "accepted"),
            "rejected": sum(1 for a in appraisals if a["decision"] != "accepted"),
            "evidence_reviews": len(reviewed), "evidence_seen": ev_seen, "evidence_approved": ev_ok,
            "pages_approved": sum(1 for r in runs if r.get("review") and mine(r["review"]["by"])),
            "changes_requested": count("new draft requested"),
            "steps_changed": count("reopened step"),
        },
        "appraisal": {"tiers": tiers,
                      "average": round(sum(a["total"] for a in appraisals) / len(appraisals), 1) if appraisals else None,
                      "ai_scores_changed": sum(1 for a in appraisals if a.get("changed"))},
    }


def owner(run: dict) -> str | None:
    """Who a run belongs to: the person who started it, else the first person who made a decision in it."""
    return run.get("started_by") or next((e["who"] for e in run["log"] if not is_automatic(e["who"])), None)


def people(run: dict) -> list[str]:
    names = [run.get("started_by")] + [e["who"] for e in run["log"] if not is_automatic(e["who"])]
    return list(dict.fromkeys(n for n in names if n))


def log(run: dict, who: str, what: str) -> None:
    run["log"].append({"time": now(), "who": who, "what": what})


# ================================================================ 1 Ingest + 2 Privacy check

def start(ws: Workspace, form: dict, text: str | None = None, url: str | None = None,
          filename: str | None = None, data: bytes | None = None, started_by: str | None = None,
          started_login: str | None = None) -> dict:
    """Create a run from a URL, an uploaded file or pasted text, then run the privacy check (no AI)."""
    f = {k: (v.strip() if isinstance(v, str) else v) for k, v in (form or {}).items()}
    f = {k: (None if v == "" else v) for k, v in f.items()}
    material = f.get("material") or "published"
    privacy = f.get("privacy") or "unknown"
    if material not in MATERIAL or privacy not in PRIVACY:
        raise AgentError("Unknown material type or privacy status.")
    url = (url or f.get("url") or "").strip() or None
    source = {"title": f.get("title"), "organisation": f.get("organisation"), "date": f.get("date"),
              "url": url, "file": filename, "language": f.get("language"), "material": material,
              "privacy": privacy, "intended_use": f.get("intended_use"), "retrieved": datetime.now().date().isoformat(),
              "reads_dutch": bool(f.get("reads_dutch")), "capture": None}
    run = {"id": ws.new_id(), "created": now(), "source": source, "question": f.get("question") or DEFAULT_QUESTION,
           "paragraphs": [], "privacy": {}, "translation": None, "appraisal": {}, "evidence": None,
           "evidence_review": None, "draft": None, "check": None, "review": None, "revision_note": None,
           "history": [], "log": [], "started_by": (started_by or "").strip() or None,
           "started_login": started_login}

    if material in RESTRICTED:  # registered by name only: the text is never read, stored or sent anywhere
        run["privacy"] = {"result": "blocked", "reason": f"{MATERIAL[material]} is restricted material. It may not be "
                          "sent to an AI service (PRD 4, Technical Blueprint 5). The content was not read or stored."}
        source["title"] = source["title"] or filename or "Restricted material"
        log(run, "agent", "registered restricted material by name only; blocked")
        return ws.save(run)

    got = T.read_source(url=url, filename=filename, data=data, text=text)
    text = got["text"]
    source["capture"] = {
        "pdf": f"Text extracted from the uploaded PDF '{filename}'. Line breaks were rebuilt into paragraphs and "
               "[Page N] marks the page; check key quotes against the PDF.",
        "file": f"Text read from the uploaded file '{filename}'.",
        "paste": "Text pasted by the researcher.",
        "pdf-link": "Downloaded PDF from the link; line breaks rebuilt into paragraphs, [Page N] marks the page. "
                    "Check key quotes against the PDF.",
        "web": "Downloaded from the link; menus and scripts removed automatically. Check key passages on the live page.",
    }[got["kind"]]
    # Details the source states about itself fill only EMPTY fields, and the note says where each came from.
    taken = []
    for key in ("title", "organisation", "date", "language"):
        found = got["details"].get(key)
        if not source[key] and found and key != "language":
            source[key] = found["value"]
            taken.append(f"{key} from {found['where']}")
    source["found_in_source"] = got["details"]
    if taken:
        source["capture"] += " Details taken from the source: " + "; ".join(taken) + "."
    text = text.replace("\r\n", "\n")
    run["paragraphs"] = T.paragraphs(text)
    if not run["paragraphs"]:
        raise AgentError("The source has no readable text.")
    source["language"] = source["language"] or got["details"]["language"]["value"]
    source["title"] = source["title"] or "(untitled)"

    signals = T.privacy_signals(text)
    if privacy == "confidential":
        run["privacy"] = {"result": "blocked", "reason": "Marked confidential: it may not be sent to an AI service."}
        run["paragraphs"] = []  # not kept
    elif privacy == "unknown" or signals or material != "published":
        reasons = (["the privacy status is not known"] if privacy == "unknown" else []) + \
                  ([f"the text contains: {', '.join(signals)}"] if signals else []) + \
                  ([f"it is: {MATERIAL[material].lower()}"] if material != "published" else [])
        run["privacy"] = {"result": "ask", "reason": "A person must decide before any AI step, because " + "; ".join(reasons) + "."}
    else:
        run["privacy"] = {"result": "clear", "reason": "Public published source; no privacy signals found."}
    if run["paragraphs"]:
        (ws.root / run["id"]).mkdir(parents=True, exist_ok=True)
        (ws.root / run["id"] / "original.txt").write_bytes(text.encode("utf-8"))
    run["translation"] = {"needed": source["language"] == "nl" and not source["reads_dutch"], "paragraphs": None}
    log(run, "agent", f"ingested ({len(run['paragraphs'])} paragraphs); privacy check: {run['privacy']['result']}")
    return ws.save(run)


def decide_privacy(ws: Workspace, run: dict, reviewer: str, allow: bool, reason: str) -> dict:
    who = check_reviewer(reviewer)
    if run["privacy"].get("result") != "ask":
        raise AgentError("This source is not waiting for a privacy decision.")
    if not (reason or "").strip():
        raise AgentError("Give a short reason for your privacy decision.")
    run["privacy"].update(result="allowed" if allow else "blocked", decided_by=who, note=reason.strip(), at=now())
    if not allow:
        run["paragraphs"] = []
        original = ws.root / run["id"] / "original.txt"
        if original.exists():
            original.unlink()
    log(run, who, f"privacy decision: {'allowed' if allow else 'blocked'} - {reason.strip()}")
    _finish_reopen(run, who, substantial=not allow, reason="privacy decision changed to blocked")
    return ws.save(run)


# ================================================================ where is the run? (drives the whole screen)

def status(run: dict) -> dict:
    """The current stage (1-9), who acts next ('ai', 'human', 'stopped', 'done') and a plain message."""
    def at(stage, who, message, task=None):
        return {"stage": stage, "who": who, "message": message, "task": task}

    p = run["privacy"].get("result")
    if p == "blocked":
        return at(2, "stopped", "Stopped by the privacy check. " + (run["privacy"].get("note") or run["privacy"]["reason"]))
    if p == "ask":
        return at(2, "human", run["privacy"]["reason"])
    if run["translation"]["needed"] and not run["translation"]["paragraphs"]:
        return at(3, "ai", "The source is Dutch: an English working translation is needed first.", "translate")
    appraisal = run["appraisal"]
    if not appraisal.get("ai"):
        return at(4, "ai", "The AI suggests scores using rubric v1.0. You decide afterwards.", "appraise")
    if not appraisal.get("human"):
        return at(4, "human", "Check the suggested scores, change any you disagree with, then approve or reject the source.")
    if appraisal["human"]["decision"] == "rejected":
        return at(4, "stopped", f"Source rejected by {appraisal['human']['by']}.")
    if run["evidence"] is None:
        return at(5, "ai", "The AI proposes evidence items. The agent checks every quote against the source.", "extract")
    if not run["evidence_review"]:
        return at(5, "human", "Tick the evidence items that may be used in the handbook.")
    if not approved_evidence(run):
        return at(5, "stopped", "No evidence was approved, so there is nothing to draft from.")
    if not run["draft"]:
        return at(7, "ai", "The AI drafts a handbook page from the approved evidence only.", "draft")
    if run.get("polish"):
        return at(7, "ai", "Style rewrite: the AI rewrites the wording so it reads less like AI. The agent refuses the "
                           "rewrite if any claim's figures, citations or block labels change.", "polish")
    if run["check"]["errors"]:
        return at(8, "human", "The automated check found problems that block approval. Ask for a new draft.")
    if not run["review"]:
        return at(9, "human", "Read the draft and the check, then approve the page or request changes.")
    return at(9, "done", f"Page approved by {run['review']['by']}. Nothing is published: publication is a separate manual step outside v0.")


def stage_states(run: dict) -> list[dict]:
    s = status(run)
    out = []
    for n, name in enumerate(STAGES, start=1):
        if n < s["stage"]:
            state = "skipped" if n == 3 and not (run["translation"] or {}).get("needed") else "done"
        elif n == s["stage"]:
            state = s["who"]
        else:
            state = "todo"
        out.append({"n": n, "name": name, "state": state})
    return out


# ================================================================ AI steps: prompt out, answer in

def _fill(template: str, values: dict) -> str:
    text = (PROMPTS / f"{template}.md").read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise AgentError(f"Prompt template {template} has unfilled fields {left}.")
    return text


def _metadata(run: dict) -> str:
    s = run["source"]
    rows = [("title", s["title"]), ("author / organisation", s["organisation"]), ("publication date", s["date"]),
            ("url", s["url"]), ("file", s["file"]), ("retrieved", s["retrieved"]), ("language", s["language"]),
            ("intended use", s["intended_use"]), ("how captured", s["capture"])]
    return "\n".join(f"- {k}: {v or 'NOT RECORDED'}" for k, v in rows)


def _paragraphs_json(run: dict, with_translation: bool = False) -> str:
    tr = (run["translation"] or {}).get("paragraphs") or {}
    items = [dict(p, english=tr.get(p["id"])) if with_translation and tr else p for p in run["paragraphs"]]
    return json.dumps(items, ensure_ascii=False, indent=1)


def prompt(run: dict, ctx: dict, ws: Workspace | None = None) -> str | None:
    """The prompt for the AI step the run is waiting for (None if it is not waiting for AI).
    `ws` gives the Stage 4 prompt the researchers' earlier appraisal decisions (calibration examples)."""
    task = status(run)["task"]
    s, dutch = run["source"], run["source"]["language"] == "nl"
    if task == "translate":
        return _fill("translate", {"RUN_ID": run["id"], "TITLE": s["title"], "PARAGRAPHS": _paragraphs_json(run)})
    if task == "appraise":
        note = ("The source is Dutch; an English working translation ('english') is included. Base your appraisal on "
                "the original and say where the translation might affect your judgement.") if run["translation"]["needed"] \
            else "You are reading the original text."
        return _fill("appraise", {"RUN_ID": run["id"], "RUBRIC": as_prompt_text(ctx["rubric"]), "CONTEXT": context_text(ctx),
                                  "TRANSLATION_NOTE": note, "METADATA": _metadata(run),
                                  "CALIBRATION": calibration_text(ws, ctx, exclude=run["id"]) if ws else NO_CALIBRATION,
                                  "PARAGRAPHS": _paragraphs_json(run, with_translation=True)})
    if task == "extract":
        h = run["appraisal"]["human"]
        return _fill("extract", {
            "RUN_ID": run["id"], "TITLE": s["title"], "ORGANISATION": s["organisation"] or "organisation not recorded",
            "TIER": h["tier"], "APPRAISAL_NOTE": h["note"] or "none", "CONTEXT": context_text(ctx),
            "FEEDBACK_NOTE": stage4_feedback_note(run),
            "QUOTE_LANGUAGE": " in its original language (Dutch)" if dutch else "",
            "TRANSLATION_RULE": "- The source is Dutch: give the English translation of each quote in \"quote_en\"." if dutch else "",
            "QUOTE_EN_FIELD": '"quote_en": "...", ' if dutch else "",
            "PARAGRAPHS": _paragraphs_json(run, with_translation=True)})
    if task == "draft":
        tier = run["appraisal"]["human"]["tier"]
        evidence = [{k: e.get(k) for k in ("id", "type", "claim", "quote", "quote_en", "paragraph", "limitation") if e.get(k)}
                    for e in approved_evidence(run)]
        return _fill("draft", {
            "QUESTION": run["question"], "CONTEXT": context_text(ctx), "TIER": tier,
            "TIER_RULE": "Tier B evidence is for background or limited claims only: state its limitations in the text."
            if tier == "B" else "Still state the limitations of the evidence.",
            "REVIEW_NOTE": run["revision_note"] or "None - this is the first draft.",
            "EVIDENCE": json.dumps(evidence, ensure_ascii=False, indent=1)})
    if task == "polish":
        d = run["draft"]
        current = {"title": d["title"], "sections": [{"purpose": x.get("purpose"), "heading": x.get("heading"),
                                                      "blocks": [{"kind": b["kind"], "text": b.get("text"), "evidence": b["evidence"]}
                                                                 for b in x.get("blocks") or []]} for x in d["sections"]],
                   "decision_questions": d["decision_questions"]}
        evidence = [{k: e.get(k) for k in ("id", "claim", "quote", "quote_en") if e.get(k)} for e in approved_evidence(run)]
        return _fill("polish", {"DRAFT": json.dumps(current, ensure_ascii=False, indent=1),
                                "EVIDENCE": json.dumps(evidence, ensure_ascii=False, indent=1),
                                "STYLE_NOTE": run["polish"].get("note") or "None."})
    return None


def parse_json(answer: str) -> dict:
    """Accept the JSON with or without ```json fences or a sentence around it."""
    text = (answer or "").strip()
    start_i, end_i = text.find("{"), text.rfind("}")
    if start_i < 0 or end_i < start_i:
        raise AgentError("No JSON found in the answer. Paste Claude's complete reply (it starts with '{').")
    try:
        data = json.loads(text[start_i:end_i + 1])
    except json.JSONDecodeError as exc:
        raise AgentError(f"The answer is not valid JSON ({exc.msg}, line {exc.lineno}). Paste the complete reply, "
                         "or ask Claude to 'reply with the JSON only'.") from exc
    if not isinstance(data, dict):
        raise AgentError("The answer must be one JSON object.")
    return data


def submit_answer(ws: Workspace, ctx: dict, run: dict, answer: str, via: str = "ai (pasted by researcher)",
                  expected_task: str | None = None) -> dict:
    """Check and store the AI answer for the current AI step. Wrong answers are refused with the reasons.
    The same checks apply whether the answer was pasted (manual mode) or came from the Claude API (automatic mode)."""
    task = status(run)["task"]
    if not task:
        raise AgentError("This run is not waiting for an AI answer.")
    if expected_task and task != expected_task:
        raise AgentError("The run changed while Claude was working (someone else may have acted on it). Reload and try again.")
    data = parse_json(answer)
    {"translate": _store_translation, "appraise": _store_appraisal, "extract": _store_evidence,
     "draft": _store_draft, "polish": _store_polish}[task](run, data, ctx)
    log(run, via, f"{task} answer accepted")
    return ws.save(run)


def _refuse(problems: list[str]) -> None:
    if problems:
        raise AgentError("The answer was not accepted:\n- " + "\n- ".join(problems[:8]) +
                         ("\n(and more)" if len(problems) > 8 else "") + "\nAsk Claude to fix these points and paste the new answer.")


def _store_translation(run: dict, data: dict, ctx: dict) -> None:
    given = {p.get("id"): (p.get("english") or "").strip() for p in data.get("paragraphs") or [] if isinstance(p, dict)}
    ids = [p["id"] for p in run["paragraphs"]]
    _refuse([f"{i} is missing or empty." for i in ids if not given.get(i)])
    warnings = [f"{p['id']}: figures differ from the original - check this paragraph."
                for p in run["paragraphs"] if T.numbers_in(p["text"]) != T.numbers_in(given[p["id"]])]
    old = ((run.get("reopened") or {}).get("saved") or {}).get("translation") or {}
    run["translation"].update(paragraphs={i: given[i] for i in ids}, uncertain_terms=data.get("uncertain_terms") or [],
                              notes=(data.get("notes") or []) + warnings,
                              title=(data.get("title") or "").strip() or run["translation"].get("title"))
    if run.get("reopened"):
        _finish_reopen(run, "ai (pasted by researcher)", substantial=old.get("paragraphs") != run["translation"]["paragraphs"],
                       reason="the translation changed")


def _store_appraisal(run: dict, data: dict, ctx: dict) -> None:
    ids = {p["id"] for p in run["paragraphs"]}
    scores, problems = {}, []
    for c in ctx["rubric"]["criteria"]:
        item = (data.get("scores") or {}).get(c["key"])
        if not isinstance(item, dict) or item.get("score") not in (0, 1, 2) or isinstance(item.get("score"), bool):
            problems.append(f"'{c['key']}' needs a score of 0, 1 or 2.")
            continue
        if not (item.get("reason") or "").strip():
            problems.append(f"'{c['key']}' needs a reason.")
        scores[c["key"]] = {"score": item["score"], "reason": (item.get("reason") or "").strip(),
                            "paragraphs": [p for p in item.get("paragraphs") or item.get("locations") or [] if p in ids],
                            "research_questions": [q for q in item.get("research_questions") or [] if q in ctx["research_questions"]]}
    if scores.get("relevance", {}).get("score") == 2 and not scores["relevance"]["research_questions"]:
        problems.append("Relevance 2 needs the research question IDs the source directly addresses.")
    _refuse(problems)
    checks = data.get("additional_checks") or {}
    total = sum(v["score"] for v in scores.values())
    run["appraisal"]["ai"] = {
        "scores": scores, "total": total, "tier": tier_for(ctx["rubric"], total),
        "checks": {k: (" - ".join(str(x) for x in (v.get("result"), v.get("note")) if x) if isinstance(v, dict) else str(v))
                   for k, v in checks.items()},
        "limitations": data.get("limitations") or [], "questions": data.get("questions_for_researcher") or [],
        "flags": _metadata_flags(run, scores)}


def _metadata_flags(run: dict, scores: dict) -> list[str]:
    s, flags = run["source"], []
    if not s["organisation"] and scores.get("authority", {}).get("score", 0) > 0:
        flags.append("Authority is above 0, but no author/organisation is recorded.")
    if not s["date"] and scores.get("recency", {}).get("score") == 2:
        flags.append("Recency is 2, but no publication date is recorded.")
    return flags


def decide_appraisal(ws: Workspace, ctx: dict, run: dict, reviewer: str, scores: dict, decision: str, note: str) -> dict:
    """The researcher's appraisal. Only this counts; the AI scores stay a suggestion."""
    who = check_reviewer(reviewer)
    st = status(run)
    if st["stage"] != 4 or st["who"] != "human":
        raise AgentError("This run is not waiting for an appraisal decision.")
    keys = [c["key"] for c in ctx["rubric"]["criteria"]]
    if sorted(scores or {}) != sorted(keys) or any(v not in (0, 1, 2) for v in scores.values()):
        raise AgentError("Give every criterion a score of 0, 1 or 2.")
    total = sum(scores.values())
    tier = tier_for(ctx["rubric"], total)
    if decision not in ("accepted", "rejected"):
        raise AgentError("Choose Approve or Reject.")
    if decision == "accepted" and tier == "C":
        raise AgentError(f"{total}/10 is Tier C: under rubric v1.0 it cannot be accepted as evidence. Reject it or change the scores.")
    changed = [k for k in keys if scores[k] != run["appraisal"]["ai"]["scores"][k]["score"]]
    if changed and not (note or "").strip():
        raise AgentError(f"You changed {', '.join(changed)}. Add a short note explaining why.")
    run["appraisal"]["human"] = {"by": who, "at": now(), "scores": scores, "total": total, "tier": tier,
                                 "changed": changed, "decision": decision, "note": (note or "").strip() or None}
    log(run, who, f"appraisal: {decision}, {total}/10 Tier {tier}" + (f" (changed {', '.join(changed)})" if changed else ""))
    record_appraisal_feedback(ws, run)
    before = (((run.get("reopened") or {}).get("saved") or {}).get("appraisal") or {}).get("human") or {}
    _finish_reopen(run, who, substantial=(before.get("decision"), before.get("tier")) != (decision, tier),
                   reason="the appraisal decision or tier changed")
    return ws.save(run)


def _store_evidence(run: dict, data: dict, ctx: dict) -> None:
    items = [i for i in data.get("evidence") or [] if isinstance(i, dict)]
    if not items:
        _refuse(["No evidence items found (expected a list under \"evidence\")."])
    by_id = {p["id"]: p["text"] for p in run["paragraphs"]}
    out = []
    for n, i in enumerate(items, start=1):
        claim, quote = (i.get("claim") or "").strip(), (i.get("quote") or "").strip()
        para = (i.get("paragraph") or i.get("location") or "").strip()
        problems = []
        if not claim or not quote:
            problems.append("claim or quote is empty")
        if not T.quote_in(quote, by_id.get(para, "")):
            found = next((pid for pid, txt in by_id.items() if T.quote_in(quote, txt)), None)
            if found:
                para = found
            else:
                problems.append("the quote was not found word for word in the source")
        extra = T.numbers_in(claim) - T.numbers_in(quote)
        if extra:
            problems.append(f"figures in the claim that are not in the quote: {', '.join(sorted(extra))}")
        out.append({"id": f"E{n}", "type": i.get("type") or "claim", "claim": claim, "quote": quote,
                    "quote_en": (i.get("quote_en") or "").strip() or None, "paragraph": para or None,
                    "research_questions": i.get("research_questions") or [], "limitation": i.get("limitation"),
                    "problems": problems, "approved": None})
    run["evidence"] = out


def decide_evidence(ws: Workspace, run: dict, reviewer: str, approved_ids: list[str]) -> dict:
    who = check_reviewer(reviewer)
    if status(run)["stage"] != 5 or status(run)["who"] != "human":
        raise AgentError("This run is not waiting for an evidence review.")
    by_id = {e["id"]: e for e in run["evidence"]}
    bad = [i for i in approved_ids if i not in by_id or by_id[i]["problems"]]
    if bad:
        raise AgentError(f"These items cannot be approved because they failed the automatic check: {', '.join(bad)}.")
    for e in run["evidence"]:
        e["approved"] = e["id"] in approved_ids
    run["evidence_review"] = {"by": who, "at": now()}
    log(run, who, f"evidence review: approved {', '.join(approved_ids) or 'none'}")
    saved = ((run.get("reopened") or {}).get("saved") or {}).get("evidence") or []
    _finish_reopen(run, who, substantial={e["id"] for e in saved if e.get("approved")} != set(approved_ids),
                   reason="a different evidence selection")
    return ws.save(run)


def approved_evidence(run: dict) -> list[dict]:
    return [e for e in run["evidence"] or [] if e["approved"]]


def _store_draft(run: dict, data: dict, ctx: dict) -> None:
    problems = []
    if not (data.get("title") or "").strip():
        problems.append("The draft needs a title.")
    sections = [s for s in data.get("sections") or [] if isinstance(s, dict)]
    if not sections:
        problems.append("The draft needs sections.")
    for s in sections:
        for b in s.get("blocks") or []:
            if b.get("kind") not in KINDS:
                problems.append(f"Unknown block kind '{b.get('kind')}' in section '{s.get('heading')}'.")
            b["evidence"] = b.get("evidence") or b.get("evidence_ids") or []
    _refuse(problems)
    run["draft"] = {"title": data["title"].strip(), "sections": sections,
                    "decision_questions": data.get("decision_questions") or [],
                    "notes_for_reviewer": data.get("notes_for_reviewer") or [], "at": now()}
    run["check"] = check_draft(run)  # stage 6 (organise) needs no action in a one-source run; stage 8 runs at once


# ================================================================ learning from appraisal decisions
# There is no model training here. "Learning" happens in the prompt: every human Stage 4 decision is
# written to a shared feedback log (AI suggestion, researcher's scores and reason), and the next Stage 4
# prompts carry a short summary of earlier corrections as calibration examples. The official rubric
# stays the only scoring framework, and every AI appraisal stays a provisional suggestion.

NO_CALIBRATION = "No earlier researcher decisions are recorded yet."
FEEDBACK_EXAMPLES = 6   # most recent corrections shown in a Stage 4 prompt
FEEDBACK_TEXT = 300     # characters kept from a researcher's note or an AI reason


def feedback_file(ws: Workspace) -> Path:
    return ws.root / "feedback" / "appraisal_feedback.jsonl"


def record_appraisal_feedback(ws: Workspace, run: dict) -> dict:
    """Append the researcher's Stage 4 decision, next to the AI's suggestion, to the feedback log."""
    ai, hm, s = run["appraisal"]["ai"], run["appraisal"]["human"], run["source"]
    entry = {"run": run["id"], "at": hm["at"], "by": hm["by"], "title": display_title(run),
             "organisation": s.get("organisation"), "material": s.get("material"), "language": s.get("language"),
             "intended_use": s.get("intended_use"), "decision": hm["decision"], "changed": hm["changed"],
             "note": hm["note"], "ai": {"total": ai["total"], "tier": ai["tier"],
                                        "scores": {k: v["score"] for k, v in ai["scores"].items()},
                                        "reasons": {k: v["reason"] for k, v in ai["scores"].items()}},
             "human": {"total": hm["total"], "tier": hm["tier"], "scores": hm["scores"]}}
    path = feedback_file(ws)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def appraisal_feedback(ws: Workspace) -> list[dict]:
    """The latest decision per run, oldest first. Runs that were deleted no longer count."""
    path, latest = feedback_file(ws), {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            latest[e.get("run")] = e
    live = set(ws.ids())
    return sorted((e for r, e in latest.items() if r in live), key=lambda e: e.get("at") or "")


def _clip(text: str | None, n: int = FEEDBACK_TEXT) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def calibration_text(ws: Workspace, ctx: dict, exclude: str | None = None) -> str:
    """Short summary of earlier researcher corrections, for the Stage 4 prompt."""
    entries = [e for e in appraisal_feedback(ws) if e["run"] != exclude]
    if not entries:
        return NO_CALIBRATION
    names = {c["key"]: c["name"] for c in ctx["rubric"]["criteria"]}
    lines = [f"Researchers have decided on {len(entries)} earlier AI appraisal suggestion(s). How often they changed "
             "the AI's score, per criterion:"]
    for key, name in names.items():
        diffs = [e["human"]["scores"][key] - e["ai"]["scores"][key] for e in entries
                 if key in e["human"]["scores"] and key in e["ai"]["scores"]]
        down, up = sum(d < 0 for d in diffs), sum(d > 0 for d in diffs)
        trend = f" (lowered {down}, raised {up})" if down or up else ""
        lines.append(f"- {name}: changed in {down + up} of {len(diffs)}{trend}")
    corrections = [e for e in entries if e["changed"]][-FEEDBACK_EXAMPLES:]
    if corrections:
        lines.append("Most recent corrections (newest last):")
        for e in corrections:
            what = "; ".join(f"{names.get(k, k)} AI {e['ai']['scores'][k]} -> researcher {e['human']['scores'][k]}"
                             f" (AI's reason: \"{_clip(e['ai']['reasons'].get(k), 160)}\")" for k in e["changed"])
            src = ", ".join(x for x in (e.get("organisation"), e.get("material")) if x)
            lines.append(f"- {e['run']} \"{_clip(e['title'], 90)}\"{f' ({src})' if src else ''}: {what}. "
                         f"Decision: {e['decision']}. Researcher's reason: \"{_clip(e.get('note')) or 'none given'}\"")
    else:
        lines.append("So far the researchers accepted every AI score unchanged.")
    agreed = sum(1 for e in entries if not e["changed"])
    if agreed and corrections:
        lines.append(f"In {agreed} of {len(entries)} decisions the researcher kept every AI score.")
    return "\n".join(lines)


def stage4_feedback_note(run: dict) -> str:
    """One line for the Stage 5 prompt: the Stage 4 decision on this source was logged as feedback."""
    ai, hm = run["appraisal"]["ai"], run["appraisal"]["human"]
    changed = (f"changed {', '.join(hm['changed'])}" if hm["changed"] else "kept every AI score")
    return (f"Stage 4 feedback logged: the AI suggested {ai['total']}/10 (Tier {ai['tier']}); the researcher "
            f"decided {hm['total']}/10 (Tier {hm['tier']}) and {changed}. This decision is stored in the appraisal "
            "feedback log and calibrates future Stage 4 suggestions. It does not change this task.")


# ================================================================ 7b optional style rewrite
# The draft's wording is rewritten to read less like AI text. The agent refuses a rewrite that changes
# any section, block label, citation or figure, so claims stay traceable to the same evidence.

def request_polish(ws: Workspace, run: dict, reviewer: str, note: str | None = None) -> dict:
    who = check_reviewer(reviewer)
    st = status(run)
    if not run["draft"] or st["who"] != "human" or st["stage"] not in (8, 9):
        raise AgentError("A style rewrite can be asked for when a draft is waiting for review.")
    run["polish"] = {"by": who, "at": now(), "note": (note or "").strip() or None}
    log(run, who, "style rewrite requested" + (f": {note.strip()}" if (note or "").strip() else ""))
    return ws.save(run)


def cancel_polish(ws: Workspace, run: dict, reviewer: str) -> dict:
    who = check_reviewer(reviewer)
    if not run.pop("polish", None):
        raise AgentError("No style rewrite is waiting.")
    log(run, who, "style rewrite cancelled; draft kept as it was")
    return ws.save(run)


def _store_polish(run: dict, data: dict, ctx: dict) -> None:
    old, problems = run["draft"], []
    new_sections = [x for x in data.get("sections") or [] if isinstance(x, dict)]
    title = (data.get("title") or "").strip()
    if not title:
        problems.append("The rewrite needs a title.")
    elif T.numbers_in(title) != T.numbers_in(old["title"]):
        problems.append("The title's figures changed.")
    if len(new_sections) != len(old["sections"]):
        problems.append(f"The rewrite has {len(new_sections)} sections; the draft has {len(old['sections'])}. Keep every section.")
    for i, (a, b) in enumerate(zip(old["sections"], new_sections), start=1):
        where = f"Section {i} ('{a.get('heading')}')"
        if b.get("purpose") != a.get("purpose"):
            problems.append(f"{where}: the purpose changed.")
        ablocks, bblocks = a.get("blocks") or [], [x for x in b.get("blocks") or [] if isinstance(x, dict)]
        if len(bblocks) != len(ablocks):
            problems.append(f"{where}: {len(bblocks)} blocks instead of {len(ablocks)}. Keep every block, in order.")
            continue
        for j, (x, y) in enumerate(zip(ablocks, bblocks), start=1):
            y["evidence"] = y.get("evidence") or y.get("evidence_ids") or []
            if y.get("kind") != x["kind"]:
                problems.append(f"{where}, block {j}: the label changed from {x['kind']} to {y.get('kind')}.")
            if list(y["evidence"]) != list(x["evidence"]):
                problems.append(f"{where}, block {j}: the citations changed ({', '.join(x['evidence']) or 'none'} expected).")
            if not (y.get("text") or "").strip():
                problems.append(f"{where}, block {j}: the text is empty.")
            elif T.numbers_in(y["text"]) != T.numbers_in(x.get("text")):
                problems.append(f"{where}, block {j}: the figures changed (expected {', '.join(sorted(T.numbers_in(x.get('text')))) or 'none'}).")
    questions = [q for q in data.get("decision_questions") or [] if isinstance(q, str) and q.strip()]
    if len(questions) != len(old["decision_questions"]):
        problems.append(f"Keep all {len(old['decision_questions'])} decision questions.")
    elif any(T.numbers_in(q) != T.numbers_in(o) for q, o in zip(questions, old["decision_questions"])):
        problems.append("A decision question's figures changed.")
    _refuse(problems)
    request = run.pop("polish")
    run["history"].append({"draft": old, "check": run["check"], "review": run["review"],
                           "style_rewrite": {"by": request["by"], "at": request["at"], "note": request.get("note")}})
    sections = [dict(a, heading=(b.get("heading") or a.get("heading")).strip(),
                     blocks=[dict(x, text=y["text"].strip()) for x, y in zip(a.get("blocks") or [], b["blocks"])])
                for a, b in zip(old["sections"], new_sections)]
    run["draft"] = dict(old, title=title, sections=sections, decision_questions=[q.strip() for q in questions], at=now(),
                        style_rewrite={"by": request["by"], "at": now()})
    run["review"] = None
    run["check"] = check_draft(run)


# ================================================================ going back to change a step
# A step that holds a decision can be reopened. When it is decided again, the new outcome is compared
# with the old one: the same outcome keeps everything after it; a different outcome clears only the
# steps that depend on it. Cleared work is kept in the run's history, never deleted.

REOPENABLE = {2: "privacy", 3: "translation", 4: "appraisal", 5: "evidence", 9: "review"}
NEXT_STAGE = {2: 3, 3: 4, 4: 5, 5: 7, 9: 10}


def _clear_from(run: dict, first: int, who: str, reason: str, keep: bool = True) -> list[str]:
    """Clear every step from `first` onward, keeping the old results in the history (unless keep=False)."""
    import copy
    parts = []
    if first <= 3 and (run["translation"] or {}).get("paragraphs"):
        parts.append("translation")
    if first <= 4 and run["appraisal"]:
        parts.append("appraisal")
    if first <= 5 and run["evidence"] is not None:
        parts.append("evidence")
    if first <= 7 and run["draft"]:
        parts.append("draft")
    if not parts:
        return []
    saved = {k: copy.deepcopy(run.get(k)) for k in ("translation", "appraisal", "evidence", "evidence_review", "draft",
                                                     "check", "review", "revision_note")}
    run["history"].append({"reset_from": first, "by": who, "at": now(), "reason": reason, "cleared": parts,
                           "data": saved if keep else None})  # blocked sources keep no text anywhere
    if first <= 3 and run["translation"]:
        run["translation"].update(paragraphs=None, title=None)
    if first <= 4:
        run["appraisal"] = {}
    if first <= 5:
        run.update(evidence=None, evidence_review=None)
    if first <= 7:
        run.update(draft=None, check=None, review=None, revision_note=None)
        run.pop("polish", None)
    return parts


def _finish_reopen(run: dict, who: str, substantial: bool, reason: str) -> None:
    r = run.pop("reopened", None)
    if not r:
        return
    if substantial:
        cleared = _clear_from(run, NEXT_STAGE[r["stage"]], who, reason, keep=r["stage"] != 2)
        log(run, who, f"step {r['stage']} changed ({reason})" + (f"; redo needed: {', '.join(cleared)}" if cleared else ""))
    else:
        log(run, who, f"step {r['stage']} confirmed without a substantial change; later steps kept")


def reopen(ws: Workspace, run: dict, reviewer: str, stage: int) -> dict:
    """Go back to a completed step to change it. Nothing after it is touched until the step is decided again."""
    import copy
    who = check_reviewer(reviewer)
    if run.get("reopened"):
        raise AgentError(f"Step {run['reopened']['stage']} is already open for changes. Finish it, or keep it as it was, first.")
    if stage not in REOPENABLE:
        raise AgentError("This step runs automatically and cannot be changed by hand.")
    tr = run["translation"] or {}
    ok = {2: run["privacy"].get("result") == "allowed",
          3: bool(tr.get("paragraphs")),
          4: bool(run["appraisal"].get("human")),
          5: bool(run["evidence_review"]),
          9: bool(run["review"])}[stage]
    if not ok:
        raise AgentError("There is no completed decision to change in this step.")
    keys = {2: ["privacy"], 3: ["translation"], 4: ["appraisal"], 5: ["evidence", "evidence_review"], 9: ["review"]}[stage]
    run["reopened"] = {"stage": stage, "by": who, "at": now(), "saved": {k: copy.deepcopy(run[k]) for k in keys}}
    if stage == 2:
        run["privacy"]["result"] = "ask"
    elif stage == 3:
        run["translation"]["paragraphs"] = None
    elif stage == 4:
        run["appraisal"]["human"] = None
    elif stage == 5:
        run["evidence_review"] = None
    elif stage == 9:
        run["review"] = None
    log(run, who, f"reopened step {stage} ({STAGES[stage - 1]}) to change it")
    return ws.save(run)


def keep_as_was(ws: Workspace, run: dict, reviewer: str) -> dict:
    """Close a reopened step without changing anything."""
    who = check_reviewer(reviewer)
    r = run.pop("reopened", None)
    if not r:
        raise AgentError("No step is open for changes.")
    run.update(r["saved"])
    log(run, who, f"closed step {r['stage']} without changes")
    return ws.save(run)


def update_details(ws: Workspace, run: dict, reviewer: str, fields: dict) -> dict:
    """Step 1: correct the source details. Details the appraisal relies on make the appraisal (and what follows) redo."""
    who = check_reviewer(reviewer)
    if run.get("reopened"):
        raise AgentError(f"Step {run['reopened']['stage']} is open for changes. Finish it first.")
    s, changed = run["source"], []
    for key in ("title", "organisation", "date", "intended_use"):
        if key in fields:
            value = (fields[key] or "").strip() or None
            if value != s.get(key) and not (key == "title" and not value):
                s[key] = value
                changed.append(key)
    if "question" in fields:
        q = (fields["question"] or "").strip() or DEFAULT_QUESTION
        if q != run["question"]:
            run["question"] = q
            changed.append("question")
    if not changed:
        return run
    if "title" in changed and run["translation"]:
        run["translation"]["title"] = None
    cleared = []
    if {"organisation", "date", "intended_use"} & set(changed):
        cleared = _clear_from(run, 4, who, "source details the appraisal relies on changed: " + ", ".join(changed))
    elif "question" in changed:
        cleared = _clear_from(run, 7, who, "the handbook question changed")
    log(run, who, "details changed: " + ", ".join(changed) + (f"; redo needed: {', '.join(cleared)}" if cleared else ""))
    return ws.save(run)


def display_title(run: dict) -> str:
    """English title when a Dutch source was translated; the original title otherwise."""
    return ((run.get("translation") or {}).get("title") or run["source"]["title"])


# ================================================================ 8 Check (automatic, no AI)

def check_draft(run: dict) -> dict:
    """Checks structure and traceability. It does NOT prove that a claim is true: a person verifies that."""
    ev = {e["id"]: e for e in run["evidence"]}
    items = []

    def add(group, level, text):
        items.append({"group": group, "level": level, "text": text})

    all_text = []
    for s in run["draft"]["sections"]:
        for b in s.get("blocks") or []:
            where, cites = f"'{s.get('heading')}'", b["evidence"]
            all_text.append(b.get("text") or "")
            unknown = [c for c in cites if c not in ev]
            unapproved = [c for c in cites if c in ev and not ev[c]["approved"]]
            if unknown:
                add("Citations & traceability", "error", f"{where} cites evidence that does not exist: {', '.join(unknown)}.")
            if unapproved:
                add("Citations & traceability", "error", f"{where} cites evidence that was not approved: {', '.join(unapproved)}.")
            if b["kind"] == "evidence" and not cites:
                add("Citations & traceability", "error", f"{where}: a factual (evidence) block has no citation.")
            support = " ".join((ev[c]["claim"] + " " + ev[c]["quote"]) for c in cites if c in ev)
            missing = T.numbers_in(b.get("text")) - T.numbers_in(support)
            if missing and b["kind"] != "example":
                add("Unsupported claims", "error", f"{where}: figure(s) {', '.join(sorted(missing))} are not in the cited evidence.")
            if b["kind"] in ("interpretation", "recommendation") and not cites:
                add("Unsupported claims", "warning", f"{where}: a {b['kind']} without any cited evidence.")
            for term in T.overgeneralisations(b.get("text")):
                add("Unsupported claims", "warning", f"{where}: '{term}' may overgeneralise.")
            for term in T.ai_style_marks(b.get("text")):
                add("Wording & style", "warning", f"{where}: {term}.")
    for where, text in [("Title", run["draft"]["title"])] + [("Decision question", q) for q in run["draft"]["decision_questions"]]:
        for term in T.ai_style_marks(text):
            add("Wording & style", "warning", f"{where}: {term}.")
    purposes = {s.get("purpose") for s in run["draft"]["sections"]}
    for key, name in REQUIRED_SECTIONS.items():
        if key not in purposes:
            add("Missing information", "warning", f"No '{name}' section.")
    if not run["draft"]["decision_questions"]:
        add("Missing information", "warning", "No decision questions for the owner.")
    missing_meta = [k for k in ("organisation", "date") if not run["source"][k]]
    if missing_meta:
        add("Missing information", "warning", f"Source metadata not recorded: {', '.join(missing_meta)}.")
    add("Needs human verification", "verify", "Check that each claim really says what its source passage says.")
    if run["source"]["language"] == "nl":
        add("Needs human verification", "verify", "The source is Dutch: check the cited quotes against the Dutch original, not only the translation.")
    if run["appraisal"]["human"]["tier"] == "B":
        add("Needs human verification", "verify", "The source is Tier B (limited use): check that its limitations are stated.")
    for note in run["draft"]["notes_for_reviewer"]:
        add("Needs human verification", "verify", f"From the draft: {note}")
    errors = sum(i["level"] == "error" for i in items)
    return {"items": items, "errors": errors, "warnings": sum(i["level"] == "warning" for i in items), "at": now(),
            "note": "The automated check confirms structure and traceability only. It does not prove claims true."}


# ================================================================ 7 again / 9 Human review

def request_new_draft(ws: Workspace, run: dict, reviewer: str, note: str) -> dict:
    """Send the page back to the AI draft step with the reviewer's notes (the old draft is kept in history)."""
    who = check_reviewer(reviewer)
    if not run["draft"]:
        raise AgentError("There is no draft yet.")
    if not (note or "").strip():
        raise AgentError("Describe what should change in the new draft.")
    run["history"].append({"draft": run["draft"], "check": run["check"], "review": run["review"],
                           "change_request": {"by": who, "note": note.strip(), "at": now()}})
    run.update(draft=None, check=None, review=None, revision_note=note.strip())
    run.pop("reopened", None)
    run.pop("polish", None)
    log(run, who, f"new draft requested: {note.strip()}")
    return ws.save(run)


def review_page(ws: Workspace, run: dict, reviewer: str, decision: str, note: str) -> dict:
    who = check_reviewer(reviewer)
    if status(run)["stage"] != 9 or status(run)["who"] != "human":
        raise AgentError("This page is not waiting for a final review.")
    if decision == "changes":
        return request_new_draft(ws, run, who, note)
    if decision != "approve":
        raise AgentError("Choose Approve or Request changes.")
    if run["check"]["errors"]:
        raise AgentError("The page still has check errors and cannot be approved.")
    run["review"] = {"by": who, "at": now(), "decision": "approved", "note": (note or "").strip() or None,
                     "publication": "Not published. Publication is a separate manual step outside v0."}
    log(run, who, "page approved (not published)")
    run.pop("reopened", None)
    return ws.save(run)
