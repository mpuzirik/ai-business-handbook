# AEL First Evaluation — Week 5

**Version 1.0** · 24 October 2026 · **Team 2:** Marija (Product manager), Diana (Tester), Maksim (Deployer), Md Samsul (Deployer), Anastasia (Researcher)

*Evaluates the team platform (`platform/` in the team repository, as uploaded on 13 October 2026) and the LLM wiki (`ael-llm-wiki`) against PRD v1.1. Goes with decision log v2.0.*

## 1. Result in one paragraph

The platform keeps its promises on traceability and human control. Quotes and figures are checked against the source, every decision stays with a researcher, and restricted material is refused before any AI sees it. Since week 5 it also learns from appraisal corrections, offers an automatic API mode with the same checks, and sends approved work to a wiki that re-checks every quote on each change. It has not shown that it saves time: no manual baseline was recorded. Dutch translation ran once but was not compared line by line with the original. The final handbook chapter was written outside the platform (T-018).

## 2. Evaluation Method

| What we planned | What we used |
|---|---|
| An institutional English report | RUN-003, JPMorganChase Institute (27 September) |
| A Dutch-language source | RUN-005, a Dutch CBS source, run live at the mini-CBI (28 September). RUN-004 (CBS, 27 September) was run by Md Samsul |
| A source that needs careful appraisal | Appraisal rules tested in code (section 3) |
| Added: automated tests | 42 tests in `platform/tests`, run on a clean copy on 24 October 2026: 42 passed |
| Added: the wiki record | RUN-001 to RUN-007 and four approved pages in `ael-llm-wiki`, checked by its GitHub Action on every push |

Each test compares the actual result with the expected result. A requirement is marked met only when the expected result was observed. Runs are as recorded in the team portfolios; the run pages in the wiki are the evidence.

## 3. Test Results

| Test | Expected result | Actual result | Status |
|---|---|---|---|
| Source appraisal | AI suggests; the researcher can change or reject it | The AI score is only a suggestion; a changed score needs a note; Tier C cannot be accepted; every correction is logged next to the AI's suggestion and shown in later appraisal prompts. Tests: `test_ai_appraisal_is_only_a_suggestion`, `test_every_appraisal_decision_is_logged_next_to_the_ai_suggestion`. First version did not learn from corrections (mini-CBI feedback, T-013) | Met, after change |
| Evidence traceability | Claims link to supporting passages | Quotes must be in the source word for word and figures must match (`test_quotes_and_figures_are_checked_against_the_source`). The wiki check compares every quote with its raw file on every push | Met |
| Dutch translation | Meaning and qualifications preserved | Dutch sources are translated before appraisal (`test_dutch_source_is_translated_before_appraisal`); a Dutch CBS source ran at the mini-CBI (RUN-005). The translation was not compared line by line with the original | Partly |
| Draft generation | Relevant section from approved evidence only | The draft may only use approved evidence (`test_draft_may_only_use_approved_evidence`). The lecturers found the first pages too AI-written; style rules and a rewrite step followed, and a rewrite that changes a figure or citation is refused (T-014) | Met, after change |
| Responsible AI | Privacy, accuracy and oversight issues identified | The draft must have a "Responsible AI" section, and the appraise, extract and draft prompts carry the project context, including its responsible-AI issues (accuracy, copyright, privacy, client confidentiality and others). The check confirms the section exists, not that its content is right | Partly |
| Human review | Researcher can correct or reject content | Page approval is a person's decision, and nothing is published (`test_page_approval_is_human_and_nothing_is_published`). Steps can be reopened; a real change redoes only the steps that depend on it | Met |
| Manual fallback | Researcher can finish a step when automation fails | Manual mode is the default and needs no API key; a scanned PDF is refused with a manual fallback; a bad API answer is refused like a pasted one | Met |
| Privacy boundary | Restricted material never reaches the AI | Restricted material is blocked and never stored; unclear privacy stops for a person; interview material never goes to the wiki (tests). Outside the platform the raw transcript was put in the team repository and in an external AI (T-017) | Met in the platform; failed in our own handling |
| Non-coder use | A teammate completes the workflow from the instructions | Md Samsul ran RUN-003 and RUN-004 and approved both pages without help (27 September). No written log of problems | Partly |
| Time per page | Less time than the manual baseline | No manual baseline was recorded | Cannot judge |

### Two checks the week 5 brief asks for

| Check | How the platform and wiki do it | Result |
|---|---|---|
| A record of each lookup: which question, which passages came back, which one was used | Every run keeps an activity log. "Send to Wiki" writes a run page with the AI's scores next to the researcher's decisions and every evidence item with its verbatim quote, marked used or not. The wiki log lists the pages read for each `/wiki` question | Met |
| A quoted passage is really in the source | Checked twice: by the platform when the answer comes in, and by the wiki check against the raw file on every push | Met |

## 4. Against the PRD Success Measures

| PRD success measure | Status |
|---|---|
| 1. Less manual repetitive work than the baseline | Not measurable: no baseline recorded |
| 2. Weekly page within the available time | Single-source pages were produced in the platform; the final chapter was not (T-018) |
| 3. Important claims traceable to an original source | Met for platform pages: quotes checked in the platform and again in the wiki |
| 4. No page published without human review | Met: no publish step; approval is a person's decision |
| 5. Unsupported claims removed or corrected | Partly: claims without approved evidence cannot enter the draft; a person reviews the rest |
| 6. A teammate completes the workflow from the instructions | Partly: done once, without a written problem log |

## 5. Problems and Improvements

| Problem found | How it was found | Change | Decision |
|---|---|---|---|
| Appraisal did not learn from researchers' corrections | Mini-CBI feedback | Corrections logged and fed into later prompts | T-013 |
| Drafted pages sounded AI-written | Mini-CBI feedback | Style rules, wording check, rewrite step | T-014 |
| Interview guide focused too much on productivity | Feedback in week 5 | Questions on knowledge gaps, postponed decisions, clients and learning added | T-015 |
| The wiki has no evidence that AI saves time in agency work | `/wiki` question in week 6 | Recorded as a research gap; the Theme 4 pilot measures time directly | T-016 |
| Raw transcript in the team repository and in an external AI | Final document review | Remove from the repository; anonymised version for AI use | T-017 |
| A source scoring 0 for Relevance can still be accepted, because the tier follows the total only | Reviewing the appraisal rule | Proposed: Relevance 0 blocks acceptance. Team to decide | Not yet logged |
| Evidence and pages stored in both the run and the wiki | Week 6 | Decide which copy leads | T-011 |
| The repository has no `.gitignore` for run folders; API keys are protected by their own folder rule | Final document review | Add a `.gitignore` for `platform/workspace/` before more runs are committed | Not yet logged |

## 6. Not Yet Tested

1. Time: a manual baseline per stage for one page, compared with a platform run.
2. Dutch translation: one translation compared line by line with the original.
3. Non-coder use with a written problem log.
4. Responsible AI: a source with a known issue, checking that the draft and the review catch it.

