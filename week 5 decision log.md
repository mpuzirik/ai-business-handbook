# AEL Decision Log — Weeks 3–5

## Purpose

This log records the important decisions in building our AI-assisted research platform: the problem, the alternatives, what we changed, what failed, and how each decision relates to the PRD. It goes with the first evaluation.

The platform is the one in `platform/` of the team repository, built by Maksim. Evidence for each entry comes from its tests (42, all passing on 24 October), its code, the team portfolios and the LLM wiki.

## Summary

| ID | When | Decision | Status |
|---|---|---|---|
| T-001 | Week 3 | Evidence retrieval architecture | In place |
| T-002 | Week 3 | Protection of field-research data | Enforced in the platform; see T-017 |
| T-003 | Week 4 | First working version V0 | Built; demonstrated at the mini-CBI |
| T-004 | Week 5 | Knowledge gaps page revised | Done |
| T-005 | Week 5 | Social media captions as first use case | Superseded by T-012 |
| T-006 | Week 5 | Human approval before publishing AI content | In the final chapter |
| T-007 | Week 5 | First evaluation of V0 | Done |
| T-008 | Weeks 3 to 5 | Manual mode first, automatic API mode added | In place; PRD v1.1 |
| T-009 | Week 3 | Nine steps instead of eight stages | In place |
| T-010 | Week 3 | One source per run | In place |
| T-011 | Weeks 3 to 6 | One run file per source, plus the LLM wiki | In place; open question |
| T-012 | October | First pilot switched to proposal preparation | In the final chapter |
| T-013 | Week 4 to 5 | Appraisal learns from researchers' corrections | Built and tested |
| T-014 | Week 4 to 5 | Pages sounded AI-written: style rules and a rewrite step | Built and tested |
| T-015 | Week 5 | Interview guide too focused on productivity | Changed |
| T-016 | Week 6 | Send to Wiki, automatic wiki check, `/wiki` questions | Built |
| T-017 | 24 Oct | Raw transcript in the team repository and in an external AI | Open |
| T-018 | October | Final chapter written outside the platform | Recorded |
| T-019 | 24 Oct | One wording for the privacy rule | Done |

---

## T-001: Evidence Retrieval Architecture

**When:** Week 3 (25 September 2026)

**Problem identified:** AI-generated articles presented confident conclusions based on different statistics and interpretations. Relying on AI summaries would make it hard to trace information back to original sources.

**Decision:** Use structured evidence records and retrieve the original appraised passages when a page is drafted.

**Alternative considered:** Pre-generated summaries as the main knowledge base.

**Reason:** Summaries can remove context and qualifications and add another layer of AI interpretation.

**PRD connection:** Source reliability, evidence traceability, human oversight.

**Status:** In place. Every evidence item carries a verbatim quote that the platform checks against the source.

## T-002: Protection of Field-Research Data

**When:** Week 3

**Problem identified:** SME interviews may contain confidential company information or personal data.

**Decision:** Raw recordings, consent documents and identifiable material stay in protected storage. Only reviewed, anonymised material enters the AI-assisted workflow.

**PRD connection:** Responsible AI, data protection, human oversight.

**Status:** Enforced in the platform, and tested:
- Identifiable transcripts, recordings and confidential information are refused at intake and never stored (`test_restricted_material_is_blocked_and_never_stored`).
- A source with unclear privacy stops for a person (`test_unclear_privacy_stops_for_a_person`).
- Research notes and interview material are never sent to the wiki (`test_research_notes_and_interview_material_never_go_to_the_wiki`).
- The Reklaame interview was recorded with consent and transcribed locally with Whisper on a team laptop. Reklaame gave written consent that covers naming the company and quoting the founder.

Outside the platform the rule was not kept once: see T-017.

## T-003: First Working Version of the Research Tool

**When:** Week 4

**Problem identified:** The documents described the platform, but we needed a working version to see whether the approach was practical.

**Decision:** Build V0 and demonstrate it to the lecturers.

**Status:** Built and demonstrated at the mini-CBI on 28 September, with a run on a Dutch CBS source (RUN-005). On 27 September Md Samsul ran two sources himself (RUN-003, JPMorganChase Institute, and RUN-004, CBS) and approved both pages under his own account. The platform was uploaded to the team repository on 13 October.

## T-004: Improving the SME Knowledge Gaps Page

**When:** Week 5

**Problem identified:** The page did not separate general research findings from assumptions about one agency.

**Decision:** Separate established findings from questions that need field research. Add preliminary priorities for business value, confidentiality, reliability, skills and cost.

**PRD connection:** Accuracy, relevance, evidence quality, usefulness.

**Status:** Done. Page v1.1 adds the interview findings, the gap that matters most now, and a link to the Theme 4 chapter.

## T-005: Social Media Content Creation as First Use Case

**When:** Week 5

**Problem identified:** Covering every AI application would make a specific, measurable recommendation impossible.

**Decision:** Focus the week 5 page on AI-assisted social media content creation.

**Alternative considered:** Customer communication, campaign analysis, automated marketing workflows.

**Status:** Superseded by T-012. The week 5 page is kept as the pre-interview version and marked as such.

## T-006: Human Approval Before Publishing AI Content

**When:** Week 5

**Problem identified:** AI content may be inaccurate, generic or off-brand.

**Decision:** AI supports drafting; employees review and approve all client-facing material.

**PRD connection:** Responsible AI, accuracy, human oversight, output quality.

**Status:** In the final chapter (section 5, Accountability) and in the pilot decision rule.

## T-007: First Evaluation of V0

**When:** Week 5

**Problem identified:** Showing that the tool runs does not show that it meets the PRD.

**Decision:** Test V0 against appraisal, traceability, Dutch translation, drafting, responsible AI, human review, manual fallback, the privacy boundary, non-coder use and time.

**Status:** Done. See the first evaluation v1.0.

## T-008: Manual Mode First, Automatic API Mode Added

**When:** Week 3 (manual mode); week 5 (automatic mode)

**Problem identified:** PRD section 5 described an agentic CLI as the engine that runs the research steps. A command line is hard for a non-coder, and an API connection needs a key and a budget.

**Decision:** The platform is built by directing Claude, as the course requires. It runs as a local web control panel, started with a double-click on `start.bat`. Every AI step works in manual mode by default: copy the prompt into Claude and paste the answer back, with no API key. In week 5 an automatic mode was added: the same prompt goes through the Claude API, and the answer passes the same checks. Mode and key are set per account; keys stay on the researcher's computer and are never shown back.

**Alternative considered:** An agentic CLI running the research steps; API-only operation.

**Evidence:** `test_settings_default_to_manual_and_never_return_the_key`, `test_automatic_mode_sends_the_same_prompt_and_its_answer_goes_through_the_same_checks`, `test_a_bad_api_answer_is_refused_like_a_pasted_one`.

**PRD connection:** Manual fallback, non-coder accessibility. The PRD was changed to v1.1 and says why.

## T-009: Nine Steps Instead of Eight Stages

**When:** Week 3

**Decision:** The platform runs nine steps: Ingest, Privacy check, Translate, Appraise, Extract evidence, Organise, Draft, Check, Human review. Eligibility is folded into the privacy check; Organise is its own step; Publish is not in the platform.

**Reason:** Publishing automatically is forbidden by the PRD. Approved pages go to the LLM wiki, and a person publishes them on the course site.

**Status:** Mapping in technical blueprint Rev 5, section 7.

## T-010: One Source per Run

**When:** Week 3

**Problem identified:** The knowledge architecture lets a draft draw on evidence from many sources. Building that first would delay a working end-to-end path.

**Decision:** One run takes one source to one reviewed page.

**Alternative considered:** Multi-source drafting from the start.

**Cost:** A platform page carries one source's evidence. Questions across sources are answered from the wiki with `/wiki` (T-016), but a multi-source handbook page is still written by the team (T-018).

## T-011: One Run File per Source, Plus the LLM Wiki

**When:** Weeks 3 to 6

**Decision:** Each run is one `run.json` with the unchanged source text, on the researcher's computer. In week 5 the team adopted the course's LLM wiki template (`ael-llm-wiki`, set up by Maksim) as the shared store: raw sources, source pages, run pages and approved handbook pages. The knowledge architecture got version 1.1 for this.

**Alternative considered:** Keeping everything in the platform's own files only.

**Open:** Evidence and handbook pages are now stored in both places. Which copy is leading is not decided (raised by Maksim in his week 6 portfolio).

## T-012: First Pilot Switched to Proposal Preparation

**When:** October 2026, after the Reklaame interview

**Problem identified:** T-005 picked social media captions before the interview. The founder said ideation and content hooks stay human, while Reklaame already uses Claude to prepare commercial proposals from its purchasing platforms.

**Decision:** The final chapter (Theme 4) recommends AI-assisted proposal preparation as the first pilot, measured against a manual baseline over ten proposals.

**Alternative considered:** Keep social media captions.

**Reason:** A pilot on a workflow the company already runs gives a real baseline and a real decision.

**Status:** In the final chapter v1.1, which is the team's fourth handbook page. The week 5 page is marked superseded.

## T-013: Appraisal Learns from Researchers' Corrections

**When:** Mini-CBI feedback (28 September), built in week 5

**What failed:** The lecturers pointed out that the appraisal step did not learn from the researchers' decisions.

**Alternative considered:** Retraining a model. Not realistic for this project.

**What we changed:** Every time a researcher changes the AI's score, the change and its reason are logged next to the AI's suggestion and shown in later appraisal prompts. A run never calibrates itself, and the rubric stays in the prompt. The researcher still decides.

**Evidence:** `test_every_appraisal_decision_is_logged_next_to_the_ai_suggestion`, `test_later_stage4_prompts_carry_the_corrections_but_keep_the_rubric`, `test_a_run_never_calibrates_itself_and_reopening_keeps_only_the_latest_decision`.

## T-014: Pages Sounded AI-Written

**When:** Mini-CBI feedback (28 September), built in week 5

**What failed:** The lecturers found the drafted pages too AI-written.

**What we changed:** The draft prompt carries writing-style rules; the check warns about AI-sounding wording; a rewrite step changes the wording only. A rewrite that changes a figure or a citation is refused.

**Evidence:** `test_the_draft_prompt_has_style_rules`, `test_the_check_warns_about_ai_sounding_wording`, `test_a_rewrite_that_changes_a_figure_or_citation_is_refused`.

## T-015: Interview Guide Too Focused on Productivity

**When:** Week 5

**What failed:** Feedback on the interview guide: it asked mostly about productivity.

**What we changed:** Questions added on what the company does not know about AI, decisions postponed for lack of information, changing client expectations, how employees learn new tools, and what AI means for junior employees.

## T-016: Send to Wiki, Automatic Wiki Check, `/wiki` Questions

**When:** Week 6

**Decision:** A "Send to Wiki" button writes each run to the LLM wiki: the AI's scores next to the researcher's decisions, every evidence item with its verbatim quote, and the approved handbook page. A GitHub Action runs the wiki check on every push: links, index, and every quote compared word for word with its raw source. If the check finds a new error, nothing is written. A `/wiki` command answers a question from the wiki only, with a citation after every claim.

**Evidence:** `test_nothing_is_written_when_the_wiki_check_finds_a_new_error`, `test_the_approved_handbook_page_goes_to_the_wiki_and_an_unchanged_run_is_not_sent_twice`. The wiki holds RUN-001 to RUN-007 and four approved pages (Maksim's week 6 portfolio).

**Finding:** Asked "What are the benefits of AI for small SMEs?", the wiki answered from three sources and said it has no evidence that AI saves time or improves quality in agency work, because all three sources are about adoption.

## T-017: Raw Transcript in the Team Repository and in an External AI

**When:** Found 24 October 2026

**What failed:** The raw, unredacted Reklaame transcript is stored in the root of the team repository (`reklaame-interview-transcript.txt`), and it was uploaded to Claude during the final document review. The course rule is that interview material never goes where an AI assistant reads it, "a private repository too". Written consent covers naming Reklaame, not this.

**What we change:**
- The transcript is handed in only where the course asks for it: in each person's portfolio on HandIn.
- Md Samsul (Deployer) removes it from the team repository.
- An anonymised version is made for any further AI use: personal remarks removed, founder referred to by role.

**Status:** Open.

## T-018: Final Chapter Written Outside the Platform

**When:** October 2026

**What happened:** The final chapter combines four sources: the interview, Noy and Zhang, the Autoriteit Persoonsgegevens and the European Commission. The platform builds one page from one source (T-010). The chapter was written by the team with general AI help for structure and wording (the chapter's AI note).

**Consequence:** The PRD hypothesis, that the platform produces handbook pages faster, is tested on single-source pages only. The evaluation says so.

## T-019: One Wording for the Privacy Rule

**When:** 24 October 2026

**Problem identified:** The rule was worded five different ways (PRD, blueprint, knowledge architecture, interview guide, T-002). The guide's "unapproved AI" was weaker than the rest.

**Decision:** Every document now uses one sentence: *Raw interview recordings, consent documents, identifiable or unredacted transcripts, and confidential client or company information must not be sent to an external AI model service. Only reviewed, anonymised material may enter the AI-assisted workflow.*
