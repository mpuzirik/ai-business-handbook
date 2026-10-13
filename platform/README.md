# AEL Research Agent v0

A simple control panel that takes **one research source** through the project workflow and **stops whenever a decision belongs to a researcher**. It follows the project documents in `../Context/` and never changes them.

## Start

1. Install **Python 3.10 or newer** (python.org; tick *"Add python.exe to PATH"*). Nothing else is needed for manual mode (automatic mode also needs `py -m pip install anthropic`, see below).
2. Double-click **`start.bat`**. Keep the black window open; the control panel opens in your browser. It runs on your computer only.
3. Create an account (first name, last name, login, password) or sign in. Then give a source (a link, a PDF or other file, or pasted text) and click **Start research**.

## How a research run works

| # | Step | Who | What happens |
|---|---|---|---|
| 1 | Ingest | agent | Reads the source (web page, PDF, Word, text) and splits it into numbered paragraphs (P1, P2 …). PDFs get a [Page N] marker per page. Missing details are flagged, never filled in. |
| 2 | Privacy check | agent → **you if unclear** | Restricted material (identifiable transcripts, recordings, confidential information) is blocked and never stored. If the status is unclear, you decide. |
| 3 | Translate | AI | Dutch sources get an English working translation. The Dutch original stays the evidence. |
| 4 | Appraise | AI suggests → **you decide** | Scores from rubric v1.0 (read live from the Search Strategy §1.1). You can change any score; Tier C cannot be approved. |
| 5 | Extract evidence | AI proposes → agent checks → **you tick** | Every quote must appear word for word in the source; every figure in a claim must appear in its quote. |
| 6 | Organise | agent | The approved evidence is numbered (E1, E2 …) and handed to the draft. |
| 7 | Draft | AI | A handbook page written from approved evidence only, with every block labelled (evidence, interpretation, assumption, recommendation, example). |
| 8 | Check | agent | Checks citations, figures, required sections and wording. It checks structure, **not truth**. Errors block approval. |
| 9 | Human review | **you** | Approve the page, or request changes (the draft goes back to step 7 with your notes). Nothing is published. |

When you enter a link or choose a file, the form fills in the details the source states about itself (author or organisation, publication date, title, language from page metadata or file properties), each with where it was found; you can change anything, and your own typing is never overwritten. On a run, click any step in the progress row for a short summary of what was done in that step. From there you can also **go back and change a step** (source details, privacy decision, translation, appraisal, evidence selection, draft, final approval). The agent compares the new outcome with the old one: the same outcome keeps everything after it; a different outcome redoes only the steps that depend on it (for example, a different appraisal tier redoes the evidence and draft). Earlier work is kept in the run's history. Dutch sources also get an English title; the original title stays visible.

After signing in you land on the **home page** (the *AEL Research Agent* button, top left, always brings you back): what is waiting for you, your recent runs, your numbers, recent team activity and a short overview of the 9 steps.

Every run is saved automatically in `workspace/`. **All research runs** (top bar) is a page listing every run, grouped by who started it, with dates, status and a search. Only the person who started a run can delete it (the bin icon only appears on your own runs; runs from before accounts count as yours if the typed name matches your full or first name). A confirmation dialog asks first (and warns if the page was approved or other people worked on it). Deleted runs go to **Recently deleted** at the bottom of that page (files in `workspace/deleted/`), visible only to the person who started them, who can **Restore** them or **Delete permanently** (a second confirmation; this removes the files). Run numbers are never reused.

**Accounts.** Everyone signs in with a login and password. Decisions and the activity log show the account's first and last name, so nobody can act under someone else's name. Passwords are stored only as salted hashes (PBKDF2) in `workspace/accounts/`; the sign-in cookie lasts 30 days and can't be read by scripts or sent by other websites. Your name button in the top bar has **Statistics** (your runs, decisions, appraisal tiers, and how often you changed the AI's suggestions), **Change password** and **Sign out**. Accounts belong to this computer's workspace; there is no password reset, so a forgotten password means creating a new account (or removing the entry from `workspace/accounts/users.json`). A draft can be downloaded as a Word file (**⬇ Download as Word**); the file states whether it is still a draft or approved, and lists the evidence behind every citation.

**AI steps** run in one of two modes, chosen with the switch on every AI step (or under your name > **AI settings**). The choice is saved per account; manual is the default.

- **Manual paste:** click *Copy prompt*, paste it into the matching chat in the team's Claude project (see `ai_step_chat_prompts.md` in the project), and paste Claude's answer back.
- **Automatic (Claude API):** click *Run with Claude* and the agent sends the same prompt to Claude for you. Needs (1) the Anthropic Python package, installed once with `py -m pip install anthropic`, and (2) a Claude API key from console.anthropic.com, entered under your name > **AI settings**, where you also pick the model (Claude Opus 5.5 by default; Sonnet 5.5 and Haiku 5.5 are cheaper). The key is stored for your account in `local_settings/claude_api.json` on this computer only. It is never shown again, never written to a run or the activity log, and `local_settings/` excludes itself from git. If the `ANTHROPIC_API_KEY` environment variable is set, it is used when no key is saved. Usage is billed to the key's account. You can still paste an answer by hand in automatic mode.

Either way the agent checks each answer the same way and refuses it, with the reasons, if something is wrong. A refused automatic answer is put in the answer box, so you can fix it and submit it by hand.

**Learning from appraisal decisions.** The AI is not retrained; it learns through its prompt. Every Stage 4 decision (the AI's scores and reasons, your scores, which ones you changed and your note) is saved in `workspace/feedback/appraisal_feedback.jsonl`. Each new Stage 4 prompt includes a short calibration section: how often researchers changed each criterion (and in which direction) plus the six most recent corrections with your reasons. The prompt says plainly that rubric v1.0 still decides and that the scores remain a suggestion. Only the latest decision per run counts, a run never calibrates itself, and deleted runs drop out. The Stage 5 prompt notes that the Stage 4 decision was logged. Short, concrete reasons when you change a score make the calibration more useful.

**Less AI-sounding pages.** The Stage 7 prompt has writing-style rules (plain, varied sentences, no filler or stock phrases, no em-dashes, concrete small-agency examples). Step 8 adds a **Wording & style** group that warns about dashes and stock phrases (warnings only, never errors). At the final review, **Rewrite to sound less AI-written** sends the draft through a separate style pass (Stage 7b). The agent refuses that rewrite if any section, block label, citation, figure or decision question changes, so claims stay tied to the same evidence. The earlier wording is kept in the run's history, and the check runs again.

**Send to wiki.** Every run has a section **LLM wiki** (published, public sources only). Enter the folder of your clone of the team wiki ([ael-llm-wiki](https://github.com/mkniazevv/ael-llm-wiki), for example cloned with GitHub Desktop) once; the panel remembers it in `local_settings/wiki.json`. **Send to wiki** then follows the wiki's own rules (its `AGENTS.md`):

- the **run page** `wiki/runs/run-NNN.md`: the inputs (source details, privacy check, question), the translation notes, the AI's appraisal scores and reasons next to the researcher's scores and decision, every proposed evidence item (ticked or not) with its verbatim quote, the draft's check, the review and the activity log;
- once the source is accepted and its evidence ticked, and if the source is not in the wiki yet: the source text in `raw/` (never overwritten) and a **source page** built from the approved evidence;
- once the final review approved the page: the **handbook page** `wiki/handbook/<title>.md`, with every block's label and citations and the quotes behind them;
- one line per page in `wiki/index.md`, one entry at the top of `wiki/log.md`, and a link from the source page to the run;
- the wiki's `tools/lint.py` runs; if the new files cause an error, everything is put back and nothing is written;
- with the tick box on, the panel first gets the latest version from GitHub (`git pull`), then commits the files and pushes them, and GitHub runs the wiki check again. This needs Git (git-scm.com); without it, commit and push from GitHub Desktop.

Send again after a later step (for example after the final review) to update the run page and add the handbook page; a run that has not changed is not sent twice. Research notes and interview material are refused. Entity and concept pages, debates and confidence need judgement across sources, so they are not written by the panel: after sending a new source, open the wiki repository with your AI assistant and ask it to finish the ingest.

## Files

```
start.bat            double-click to start
app.py               the control panel's small web server (no research rules here)
agent/workflow.py    the whole workflow: steps, checks and human decision points
agent/rubric.py      reads the rubric from ../Context/week 2 search strategy.md
agent/text.py        reading links and files, paragraphs, quote and privacy checks
agent/word.py        Word (.docx) export of a draft page
agent/accounts.py    accounts, password hashing and sign-in sessions
agent/claude_api.py  automatic mode: AI settings per account and the call to the Claude API
agent/wiki.py        Send to wiki: run pages, source pages and handbook pages in the team's LLM wiki
agent/vendor/        bundled pypdf (BSD licence) for reading PDFs, so nothing has to be installed
agent/prompts/       the AI prompts (translate, appraise, extract, draft, polish = style rewrite)
local_settings/      your AI settings, API key and wiki folder (created when you save them; never commit)
context/             project context used in the prompts (research questions, scope rules)
ui/                  the screen (HTML, CSS, JavaScript)
tests/               proof of the key rules:  python -m unittest discover tests
workspace/           your research runs, one folder each (run.json + the original text),
                     and feedback/appraisal_feedback.jsonl (the Stage 4 decisions used for calibration)
```

## Not in v0

Publishing handbook pages, a database, online hosting, password reset, scanned PDFs without a text layer (paste the text instead), and combining several sources into one page.
