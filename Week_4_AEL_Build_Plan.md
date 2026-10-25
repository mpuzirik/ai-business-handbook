# AEL Build Plan

Built first: the source record (Phase 1), because every later step reads it. A change is kept only after the platform's tests pass, then its commit, then its merge to `main`. Now: Phases 1 to 8 are built and in `main` of the team repository. Phase 9 (time baseline and the open fixes) is next.

## Header

| Field | Value |
| --- | --- |
| Platform | AEL Research Agent v0: one source in, one traceable handbook page out (`platform/` in the team repository), with the LLM wiki `ael-llm-wiki` as shared store |
| Team and build roles | Marija: Product manager · Diana: Tester · Maksim: Deployer · Md Samsul: Deployer · Anastasia: Researcher |
| Holds the pen | Md Samsul, Marija |
| Ticks the boxes | Diana (Tester), at the end of every working session and at every merge |
| Version | Build plan v1.1, 24 October 2026 (week 4 document; rewritten for the team platform) |
| Builds from | PRD v1.1 · Technical Blueprint Rev 5 · Knowledge Architecture v1.1 · search strategy section 1.1, rubric v1.0 · decision log v2.0 (T-###) |
| Code baseline | The platform as uploaded to the team repository on 13 October 2026; 42 tests |
| Copy for the assistant | This file, in the team repository. The assistant reads it before any change |

## Where the build is now

Phases 1 to 8 are built, tested and in `main` of the team repository (uploaded 13 October). All 42 tests passed on a clean copy on 24 October. Phase 9 is partly done: the raw transcript was deleted from the repository (P9.1) and a root `.gitignore` keeps run folders, local settings and interview files out (P9.3), both on 25 October. Still open: the time baseline, the translation check and the non-coder problem log.

| Phase | What a person can do at the end | Test gate | Commit gate | Push gate |
| --- | --- | --- | --- | --- |
| 1 Source record | Turn a link, PDF or text into an identified, numbered source | Passed | In `main` | In `main` |
| 2 Privacy line | See restricted material refused before any AI sees it | Passed | In `main` | In `main` |
| 3 Appraisal | Approve a source with rubric v1.0, overruling the AI with a note | Passed | In `main` | In `main` |
| 4 Evidence | Get claims whose quotes and figures are proven in the source | Passed | In `main` | In `main` |
| 5 Reviewed page | Approve a checked page and export it | Passed | In `main` | In `main` |
| 6 Teammate runs it alone | Start the panel with a double-click and run a source without help | Passed | In `main` | In `main` |
| 7 Mini-CBI feedback | Appraisal learns from corrections; pages rewritten without AI wording; optional API mode | Passed | In `main` | In `main` |
| 8 Shared and checked | Send a run to the wiki, have every quote re-checked, ask the wiki a question | Passed | In `main` | In `main` (wiki in its own repository) |
| 9 Measured and cleaned up | Show time saved; transcript out of the repository; run folders ignored | P9.1, P9.3 passed | P9.1, P9.3 in `main` | P9.1, P9.3 in `main` |

Commit evidence: the dates and test results are below. Commit hashes are in the repository history, which a ZIP download does not include.

## The rules

Every change passes three gates in this order: test, commit, push. Team members and the AI assistant follow the same steps, word for word.

### 1. Test gate: what to run

1. Open a terminal in `platform/`.
2. Run `python -m pytest -q tests` (on Windows: `py -m pytest -q tests`).
3. For a wiki change, run `python tools/lint.py` in the wiki folder. It must report 0 errors; the GitHub Action runs the same check on every push.
4. Do the manual check written beside the task: the steps, and what you should see.
5. Passing = pytest prints `N passed` with 0 failed, the lint reports 0 errors, AND the manual check shows the stated result.
6. Write beside the box: date · commit or pull request · what the test showed. A failed attempt is written too and is never deleted.

A bug fix or new feature adds its own test to `platform/tests/` first. It passes only when that new test passes as well.

### 2. Commit gate: when to commit

- **Nothing is committed until its test gate has passed.**
- One task = one commit. Message: `P<phase>.<task>: <what changed>`, for example `P9.3: ignore platform/workspace`.
- Never commit run folders, accounts, API keys or interview material. The root `.gitignore` keeps run folders, local settings and interview files out (P9.3). A file that is already committed must be deleted by hand, as the transcript was (P9.1).
- Test fails: the change is not committed. Fix it and run the gate again.
- Fails twice in a row: stop. Put the working copy back with `git restore .`, write both failures beside the box, and post them in the team chat to Marija (Product manager). A third attempt only after the team agrees a different approach, or the task is split.

### 3. Push gate: when to push

- Work on a branch named `p<phase>-<short-name>`. When every task in the phase is committed, push the branch and open a pull request to `main`.
- **Md Samsul (Deployer) merges in the team repository; Maksim (Deployer) merges in the wiki repository.** Before merging, the one who merges runs the test gate on their own laptop and checks that `start.bat` opens the panel.
- After the merge and push, every member pulls and says "pulled" in the team chat. Then Diana ticks the push gate.
- **The next phase starts only after a successful merge and push, and everyone has pulled.**
- Merge conflicts or tests fail after merging: nothing is pushed (`git merge --abort`). The branch owner updates the branch from `main`, reruns the test gate and asks again. The waiting phase stays not started.
- Second failed merge for the same phase: the phase goes back to its last open task, and Marija decides whether to split it.
- `main` breaks after a push, or the wiki check turns red: the one who merged reverts it the same day (`git revert -m 1 <merge commit>`). That counts as one failed merge.

### Who ticks, and when

Diana (Tester) ticks every task and gate box at the end of each working session and at each merge. The one who merged sends her the commit or pull-request link. An unticked box means not done; a ticked box always has its evidence line.

## Phases

Phase 1 is built first because every later step reads the source record (blueprint section 3), and reading any web page, PDF or Word file was the part most likely to prove impossible. Phases 1 to 5 run in order: each step's output is the next step's input. Phase 6 needs 1 to 5; Phases 7 and 8 need 6 and can run side by side. Each phase fits one week or less.

Boxes for Phases 1 to 8 were ticked on 24 October from the tests, the code and the team portfolios; Diana confirms them at the next session. Evidence line: date · commit or pull request · what the test showed.

### Phase 1: a link, PDF or text becomes an identified, numbered source

Needs: nothing. Week 3.

- [x] P1.1 Read a link, PDF or pasted text into numbered paragraphs; refuse a scanned PDF with a manual fallback. *Deployer, Maksim* · `agent/text.py`, blueprint Ingest · tests `test_pdf_upload_is_read_with_pages_and_paragraphs`, `test_scanned_pdf_is_refused_with_a_manual_fallback`
- [x] P1.2 Record title, organisation, date, language and material type in the run file. *Deployer, Maksim* · `agent/workflow.py`, blueprint source-record contract
- [x] P1.3 Show an English title for a Dutch source. *Deployer, Maksim* · `agent/workflow.py` · test `test_dutch_title_is_translated_for_display`
- [x] **Test gate.** Run pytest; then add a web link and a PDF; pass = each shows title, language and numbered paragraphs. *Tester, Diana* · 27 Sep: RUN-003 (JPMorganChase Institute) and RUN-004 (CBS) ingested · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` since 13 Oct (platform upload). A test run before that commit was not recorded
- [x] **Push gate.** Pushed to `main` 13 Oct. Who pulled was not recorded

### Phase 2: restricted material is refused before any AI sees it

Needs: Phase 1's source record. Week 3.

- [x] P2.1 Material type chosen at intake; identifiable transcripts, recordings and confidential information refused and never stored. *Deployer, Maksim* · `agent/workflow.py`, blueprint Eligibility / Privacy Check · test `test_restricted_material_is_blocked_and_never_stored`
- [x] P2.2 Privacy signals or "not sure" stop the run for a person. *Deployer, Maksim* · `agent/text.py` · test `test_unclear_privacy_stops_for_a_person`
- [x] P2.3 Blocking a source later removes its text everywhere. *Deployer, Maksim* · `agent/workflow.py` · test `test_blocking_on_second_thought_removes_the_text_everywhere`
- [x] **Test gate.** Run pytest; then start a run marked "identifiable transcript"; pass = refused, nothing stored. *Tester, Diana* · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 3: a researcher approves a source with rubric v1.0, overruling the AI with a note

Needs: a source that passed Phase 2. Week 3.

- [x] P3.1 Read rubric v1.0 live from search strategy section 1.1. *Deployer, Maksim* · `agent/rubric.py`, `context/project_context.json` · test `test_rubric_is_read_from_the_project_document`
- [x] P3.2 Translate a Dutch source before appraisal; the original stays the evidence. *Deployer, Maksim* · `agent/prompts/translate.md` · test `test_dutch_source_is_translated_before_appraisal`
- [x] P3.3 AI suggests scores; the researcher decides; a changed score needs a note; Tier C cannot be accepted. *Deployer, Maksim* · `agent/prompts/appraise.md`, `agent/workflow.py` · test `test_ai_appraisal_is_only_a_suggestion`
- [x] **Test gate.** Run pytest; then change one AI score without a note; pass = refused; with a note it saves. *Tester, Diana* · 28 Sep: RUN-005, a Dutch CBS source, run at the mini-CBI · 24 Oct: 42/42 passed. Not yet done: the translation compared line by line with the original (P9.2)
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 4: claims come back with quotes and figures proven in the source

Needs: an accepted appraisal from Phase 3. Week 3.

- [x] P4.1 Every quote must be in the source word for word, and every figure in the claim must be in the quote. *Deployer, Maksim* · `agent/workflow.py`, `agent/text.py` · test `test_quotes_and_figures_are_checked_against_the_source`
- [x] P4.2 The researcher approves evidence item by item; failed items cannot be approved. *Deployer, Maksim* · `agent/prompts/extract.md`, `agent/workflow.py`
- [x] **Test gate.** Run pytest; then paste an answer with one figure changed; pass = refused with the item named. *Tester, Diana* · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 5: a researcher approves a checked page and exports it

Needs: approved evidence from Phase 4. Week 3.

- [x] P5.1 Draft from approved evidence only, with Opportunities, Limitations, Responsible AI and Actions sections. *Deployer, Maksim* · `agent/prompts/draft.md` · test `test_draft_may_only_use_approved_evidence`
- [x] P5.2 Page approval by a person; nothing is published. *Deployer, Maksim* · `agent/workflow.py` · test `test_page_approval_is_human_and_nothing_is_published`
- [x] P5.3 Reopen a step: no real change keeps later steps, a real change redoes them. *Deployer, Maksim* · `agent/workflow.py` · tests `test_going_back_without_a_real_change_keeps_later_steps`, `test_a_real_change_redoes_the_steps_that_depend_on_it`
- [x] P5.4 Word export. *Deployer, Maksim* · `agent/word.py`
- [x] **Test gate.** Run pytest; then approve a page; pass = status says approved and nothing published. *Tester, Diana* · 27 Sep: RUN-003 and RUN-004 pages approved by Md Samsul · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 6: a teammate starts and runs the platform alone

Needs: Phases 1 to 5. Week 3.

- [x] P6.1 Double-click `start.bat` opens the panel; manual mode needs no API key. *Deployer, Maksim* · `platform/start.bat`, `app.py`
- [x] P6.2 Accounts: every decision under a real name; passwords never stored. *Deployer, Maksim* · `agent/accounts.py` · test `test_accounts_protect_names_and_never_store_passwords`
- [x] **Test gate.** A teammate runs two sources without help. *Tester, Diana* · 27 Sep: Md Samsul ran RUN-003 and RUN-004 and approved both pages under his own account. No written problem log (P9.4)
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 7: the mini-CBI feedback is built in

Needs: Phase 6. Week 5. Can run beside Phase 8.

- [x] P7.1 Appraisal learns from researchers' corrections, shown in later prompts (T-013). *Deployer, Maksim* · `agent/workflow.py` · 5 tests in `test_feedback_api_style.py`
- [x] P7.2 Writing-style rules, a wording check and a rewrite step that keeps every figure and citation (T-014). *Deployer, Maksim* · `agent/prompts/draft.md`, `agent/prompts/polish.md` · tests `test_a_rewrite_that_changes_a_figure_or_citation_is_refused` and 3 more
- [x] P7.3 Automatic mode through the Claude API, same prompt and same checks; manual stays the default (T-008). *Deployer, Maksim* · `agent/claude_api.py` · 5 tests
- [x] **Test gate.** Run pytest; then change an AI score and start a new appraisal; pass = the correction appears in the new prompt. *Tester, Diana* · First failure: the lecturers found the appraisal did not learn and the pages sounded AI-written (28 Sep) · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` since 13 Oct
- [x] **Push gate.** Pushed to `main` 13 Oct

### Phase 8: the work is shared and re-checked automatically

Needs: Phase 6. Weeks 5 and 6. Can run beside Phase 7.

- [x] P8.1 Team repository with the platform under `platform/`. *Deployer, Md Samsul* · team repository · 13 Oct upload
- [x] P8.2 LLM wiki from the course template, with a GitHub Action running the wiki check on every push (T-011, T-016). *Deployer, Maksim* · `ael-llm-wiki`
- [x] P8.3 "Send to Wiki": run page, source page, raw file and approved page; interview material never sent; nothing written if the check finds a new error. *Deployer, Maksim* · `agent/wiki.py` · 7 tests in `test_wiki.py`
- [x] P8.4 `/wiki` command: questions answered from the wiki only, with citations. *Deployer, Maksim* · wiki repository
- [x] **Test gate.** Run pytest and the wiki check; pass = 0 errors. *Tester, Diana* · Week 6: RUN-001 to RUN-007 and four approved pages in the wiki · 24 Oct: 42/42 passed
- [x] **Commit gate.** In `main` of both repositories
- [x] **Push gate.** Pushed; the wiki badge shows the check result

### Phase 9: time saved is measured, and the open fixes are done

Needs: Phases 7 and 8. Before the final assessment.

- [x] P9.1 Remove the raw interview transcript from the team repository; it goes only into the HandIn portfolio (T-017). *Deployer, Md Samsul* · repository root. Test: the file is gone from `main`; a search for "Reklaame interview" finds no transcript · 25 Oct: deleted from `main`. Older commits still hold it
- [ ] P9.2 Compare one Dutch translation line by line with the original. *Tester, Diana* · RUN-005. Test: every qualification in the original is in the translation, or the gap is written down
- [x] P9.3 Add a `.gitignore` for `platform/workspace/`. *Deployer, Md Samsul* · `.gitignore`. Test: a new run folder does not show in `git status` · 25 Oct: passed; run folders, `platform/local_settings/` and transcript files are ignored
- [ ] P9.4 A teammate runs one source from the README alone; Diana writes down every place they get stuck. *Tester, Diana* · `README.md`. Test: run reaches "Page approved"; problems listed
- [ ] P9.5 Record the manual time per stage for one page and compare it with a platform run. *Product manager, Marija* · new `BASELINE.md`. Test: minutes per stage, manual against platform
- [ ] **Test gate.** P9.1 to P9.5 pass. *Tester, Diana*
- [ ] **Commit gate.** One commit per task. *Deployer, Md Samsul*
- [ ] **Push gate.** Merged, pushed, everyone pulled. *Deployer, Md Samsul*

Publishing a handbook page on the course site is not built: it stays a manual step by a person (T-009).

## Trace to the blueprint and the PRD

Every blueprint part is built in a phase except Publish, which stays manual on purpose. Every test gate checks a quality the PRD names.

### Blueprint parts → phase

| Blueprint part (Rev 5) | Built in | Note |
| --- | --- | --- |
| Ingest | P1 | |
| Source-record contract (section 3) | P1, extended in P3 | Appraisal fields added in P3 |
| Eligibility / Privacy Check | P2 | Eligibility folded into the privacy step (T-009) |
| The line nothing may cross (section 5) | P2, P8.3, P9.1 | Interview material never sent to the wiki; transcript deleted from the repository on 25 October (older commits still hold it) |
| Shared context file (section 4) | P3 | `context/project_context.json`; the rubric is read live |
| Translate if required | P3 | Line-by-line comparison still open (P9.2) |
| Human Appraise, rubric v1.0 | P3, P7.1 | |
| Extract Evidence | P4 | |
| Evidence record (Knowledge Architecture, T-001) | P4, P8.3 | Stored in the run and in the wiki (T-011) |
| Draft | P5, P7.2 | |
| Check: automated checks (section 6) | P5, P8.2 | Quotes checked in the platform and again in the wiki |
| Check: human Tester review (section 6) | P5 | Page approval by a person |
| Publish | Not built | Manual step on the course site. Reason: the PRD forbids automatic publication |

### PRD qualities → test gate

| PRD quality | Where the PRD says it | Gate that tests it |
| --- | --- | --- |
| Sources added and identified | Workflow 1 and 2 | P1 |
| Restricted material never reaches an external AI | Section 4, risk table | P2, P8, P9.1 |
| Researcher can change or reject the appraisal | Workflow 4, human oversight | P3, P7 |
| Dutch original kept, translation traceable | Workflow 3, risk table | P3, P9.2 |
| Every claim linked to its source; AI cannot change a fact | Workflow 5, success measure 3 | P4, P8 |
| Draft only from selected evidence; unsupported claims caught | Workflow 7 and 8, success measure 5 | P5, P7 |
| No page published without human review | Section 2.9, success measure 4 | P5 |
| Manual fallback for every AI step | Section 4 | P1, P6, P7.3 |
| A non-coder completes the workflow | Section 4, success measure 6 | P6, P9.4 |
| Less repetitive work; weekly page within time | Success measures 1 and 2 | P9.5 |

## Decisions and open questions

### Decisions

| Decision | Option turned down | What it costs |
| --- | --- | --- |
| B1: manual copy-paste mode first, automatic API mode added later (T-008) | API-only from the start | Every AI step was pasted by hand until week 5; less time saved for success measure 1 |
| B2: publishing stays a manual step (T-009) | Automatic publishing to the course site | One manual step per page, but no page can go out without a person |
| B3: one source per run (T-010) | Pages built from several sources | A platform page carries one source's evidence; the final chapter was written outside the platform (T-018) |

### Open questions

| Question | Owner | When |
| --- | --- | --- |
| Which copy of the evidence leads: the run on a researcher's computer or the wiki? (T-011) | Maksim | Before the final assessment |
| Should a source with Relevance 0 be blocked from acceptance, even if its total reaches Tier B? | Marija | Before the final assessment |
| Who makes the anonymised transcript for any further AI use? (T-017) | Md Samsul | Before the final assessment |
| Does the course site accept the Theme 4 chapter as is (Word), with its source links? | Md Samsul | Before the final assessment |
