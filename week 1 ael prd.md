# AEL Product Requirements Document — Revised Draft

*Revised after module-owner questions. The open questions in this document will be revisited in the Week 2 technical blueprint.*

## 1. Problem and Users

The purpose of the platform is to support our research team in researching, writing, reviewing and publishing an evidence-based handbook about the practical use of AI in small marketing and advertising agencies.

The platform should help transform reliable research material into one reviewed handbook page each week while reducing repetitive research and writing work.

### Primary User: Research Team

The research team will use the platform to:

* add and organise sources;
* process Dutch and English information;
* appraise source quality;
* extract useful evidence;
* connect evidence to research questions;
* create a first handbook-page draft;
* check the draft for problems;
* review and edit the output;
* and prepare approved content for publication.

The platform supports the researchers but does not replace their judgement.

### Downstream User: SME Owner

The final reader is an owner or manager of a small marketing or advertising agency.

The SME owner will not operate the research platform directly. Instead, the platform helps the research team produce handbook pages that support practical decisions about where AI could create business value and where its use may introduce unacceptable risks.

---

## 2. Core User Workflow

The platform must support the following path from research material to a reviewed handbook page.

### 1. Add Source Material

The researcher can add material such as:

* URLs;
* reports;
* PDFs;
* research papers;
* Dutch and English articles;
* company information;
* approved research notes.

### 2. Identify the Source

The platform should capture basic source information, including:

* title;
* author or organisation;
* publication date;
* source type;
* original language.

### 3. Translate When Necessary

If a source is in Dutch, the platform may create an English working translation or summary while keeping the original Dutch source available.

Important claims must remain traceable to the original material.

### 4. Appraise the Source

The platform should assist the researcher in evaluating a source according to:

* authority;
* relevance;
* recency;
* evidence quality;
* possible bias.

The platform may suggest an appraisal, but the researcher must be able to change or reject it.

### 5. Extract Evidence

The platform should identify potentially useful:

* claims;
* statistics;
* examples;
* findings.

Every extracted item must remain linked to its original source.

### 6. Organise Evidence

Evidence should be connected to relevant:

* research questions;
* handbook topics;
* external or internal analysis;
* responsible-AI issues.

### 7. Generate a First Draft

The platform may generate a first English-language handbook-page draft using only selected evidence.

### 8. Check the Draft

Before human approval, the platform should help identify:

* unsupported claims;
* missing or weak citations;
* unclear wording;
* possible factual inconsistencies;
* missing responsible-AI considerations;
* content that is not useful to the SME owner.

### 9. Human Review and Publication

A researcher must review and approve the final page.

**No handbook page may be published automatically without human approval.**

---

## 3. Required Output Quality

A good handbook page must:

* use clear English suitable for a non-technical SME owner;
* answer a practical business question;
* use reliable and relevant evidence;
* provide traceable sources for important claims;
* distinguish evidence from assumptions;
* include realistic examples for small marketing agencies;
* explain both opportunities and limitations;
* address responsible-AI issues where relevant;
* avoid unsupported AI-generated claims;
* explain business implications rather than only technology;
* provide useful actions, recommendations or decision questions;
* and remain concise and easy to scan.

These requirements correspond with the quality criteria in the AIBS research proposal.

---

## 4. Constraints and Boundaries

### Existing Website

The project will reuse the existing course website/wiki.

A new CMS or website will not be created.

### Non-Coder Accessibility

The main workflow must be usable by a team member without programming experience.

Commands and outputs should therefore be simple and understandable.

### Human Oversight

Important decisions remain human responsibilities, including:

* accepting or rejecting a source;
* changing a source appraisal;
* interpreting research findings;
* approving recommendations;
* and approving publication.

### Interview and Confidential Material

Raw interview recordings, identifiable interview transcripts and confidential company information must **not be sent to an external or free-tier AI model service**.

If interview evidence is later used in the research workflow, it must first follow the agreed consent, anonymisation and data-handling process.

This boundary will be shown explicitly in the Week 2 technical blueprint.

### Manual Fallback

Important automated steps must have a manual alternative.

For example, if automatic extraction, translation or drafting fails, the researcher must still be able to continue the workflow manually.

---

## 5. Why Use an Agentic CLI?

The team will use an agentic CLI where it provides useful coordination across multiple research steps.

The important capabilities are not simply generating text. The platform needs to be able to:

* follow a repeatable multi-step workflow;
* read project context and research criteria;
* process different source files;
* extract structured information;
* apply the same source-appraisal criteria consistently;
* connect evidence to research questions;
* create files in agreed formats;
* run checks before drafting or publication;
* and preserve links between evidence and sources.

Tasks involving judgement, such as deciding whether a source is trustworthy or whether a claim is sufficiently supported, must not be delegated completely to the agent.

The agent may make a recommendation, but a researcher must make the final decision.

---

## 6. Hypothesis and Success Measures

### Hypothesis

**Using the research platform will reduce repetitive work in the research-to-draft process while maintaining or improving the traceability and quality of evidence used in handbook pages.**

### Baseline

Before relying on the platform, the team will record how long it takes to complete the main stages manually for a handbook page:

* finding and processing sources;
* appraising sources;
* extracting evidence;
* organising evidence;
* preparing a first draft;
* checking citations and claims.

### Success Measures

The platform will be considered useful if:

1. it reduces the amount of manual repetitive work compared with the recorded baseline;
2. the team can produce the required weekly handbook page within the available working time;
3. important factual claims in the final page remain traceable to an original source;
4. no handbook page is published without human review;
5. unsupported or unverifiable claims identified during review are removed or corrected;
6. a non-coder team member can complete the main workflow using the instructions provided.

The first measured workflow will establish the baseline. After that baseline exists, the team can set a realistic percentage target for time reduction rather than inventing a target without evidence.

---

## 7. Content Risks and Mitigations

| Risk                                                          | Mitigation                                                                                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| AI invents or changes a fact                                  | Important claims must be checked against the original source before publication.                                                           |
| AI creates a citation that does not support the claim         | Citations must remain linked to the source evidence and receive human verification.                                                        |
| Weak or biased sources are treated as reliable                | Sources are appraised using authority, relevance, recency, evidence quality and possible bias. Human researchers can reject the appraisal. |
| Translation changes the meaning of a Dutch source             | Original Dutch content is retained and important translated claims can be compared with it.                                                |
| Drafting overstates what the evidence proves                  | The final review checks whether conclusions match the strength and scope of the evidence.                                                  |
| AI output becomes generic or unsuitable for an SME owner      | The page is checked against the handbook quality criteria before approval.                                                                 |
| Confidential information is exposed to an external AI service | Raw confidential and identifiable interview material does not cross the defined data boundary.                                             |

---

## 8. Assumptions and Consequences

| Assumption                                                             | If the assumption is wrong                                                                                                                   |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Small marketing agencies can benefit from some forms of generative AI. | The handbook must report that evidence honestly and avoid recommending AI where business value cannot be demonstrated.                       |
| Enough useful Dutch and English sources can be found.                  | The research scope will expand to suitable European or international sources while keeping relevance to Dutch SMEs clear.                    |
| The existing website can accept the platform's final output.           | The output format will be changed to whatever format the existing website requires.                                                          |
| Researchers will review every page before publication.                 | Publication must remain blocked until a human review step has been completed.                                                                |
| Markdown is a suitable working format.                                 | Another simple structured format will be selected and the relevant platform output changed.                                                  |
| The SME visit will provide useful internal information.                | Internal conclusions will be limited to evidence actually collected, with greater reliance on desk research and documented comparable cases. |

---

## 9. Open Questions and Next Steps

| Open Question                                         | Next Step                                                                                                   | Responsible Role          | Target                                     |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------ |
| Which agentic CLI will be used?                       | Compare the available option against the required workflow and choose the simplest suitable tool.           | Developer                 | Week 2                                     |
| How will sources and extracted evidence be stored?    | Define a simple structured file format and show it in the technical blueprint.                              | Developer                 | Week 2                                     |
| How will source reliability be assessed consistently? | Convert the AIBS quality criteria into a repeatable appraisal checklist.                                    | Research team             | Week 2                                     |
| How will confidential interview material be handled?  | Define the consent, anonymisation and model-service boundary before field research is processed.            | Whole team                | Before SME interview material is processed |
| How much translation should be automated?             | Test a Dutch source and compare the automated working summary with the original.                            | Research team             | Week 2–3                                   |
| How will citations be generated and checked?          | Define how extracted evidence keeps its source reference and how humans verify it.                          | Developer + research team | Week 2                                     |
| Which parts should be automated first?                | Prioritise the steps that remove repetitive work without removing human judgement.                          | Whole team                | Week 2                                     |
| How will non-coder usability be tested?               | Have a non-coder team member complete the workflow using only the written instructions and record problems. | Non-coder tester          | Week 3                                     |

These open questions will be revisited in the technical blueprint and later project documents as decisions are made.

