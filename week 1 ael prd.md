# AEL Product Requirements Document — First Draft

## 1. Problem and Users

The purpose of the platform is to support our research team in researching, writing and publishing an evidence-based handbook about the practical use of AI in small marketing and advertising agencies.

The platform will help transform raw research material into one new published handbook page each week.

There are two main user groups.

### Primary User: Research Team

The research team uses the platform to:

* collect sources;
* process Dutch and English information;
* evaluate sources;
* extract useful evidence;
* organise research;
* create draft handbook pages;
* review the output;
* and publish approved pages.

The platform should reduce repetitive research and writing work while keeping researchers responsible for final decisions.

### Downstream User: SME Owner

The final reader is an owner or manager of a small marketing or advertising agency.

The SME owner does not directly need to operate the research platform.

Instead, they receive the handbook produced using the platform.

The handbook should help them make practical decisions about where AI could create business value and where its use may introduce unacceptable risks.

## 2. What the Platform Must Let a User Do

The platform must support the complete path from raw research material to a published handbook page.

The expected workflow is:

**1. Add source material**

The user can provide material such as:

* URLs;
* reports;
* PDFs;
* research papers;
* Dutch or English articles;
* company information;
* interview transcripts;
* interview notes.

**2. Identify and process the source**

The platform identifies:

* source title;
* author or organisation;
* publication date;
* source type;
* original language.

**3. Translate when necessary**

If the source is in Dutch, the platform creates an English translation or English working summary while keeping access to the original Dutch content.

**4. Appraise the source**

The platform helps evaluate the source based on:

* authority;
* relevance;
* recency;
* evidence quality;
* potential bias.

The researcher must still be able to manually change or reject the appraisal.

**5. Extract evidence**

The platform identifies claims, statistics, examples and findings that may help answer the research questions.

Evidence should stay connected to its original source.

**6. Organise evidence by research question**

The platform helps connect evidence to:

* external-analysis questions;
* internal-analysis questions;
* handbook topics;
* responsible-AI issues.

**7. Generate a handbook-page draft**

The platform uses the selected evidence to produce a first English-language draft.

**8. Check the draft**

Before publication, the platform should help check:

* clarity;
* factual support;
* missing citations;
* responsible-AI coverage;
* usefulness to the SME owner;
* unsupported claims.

**9. Human review**

A team member reviews and edits the draft.

No page should be published automatically without human approval.

**10. Publish**

The approved page is added to the existing course wiki/site.

The project will reuse the existing infrastructure rather than create a new publishing system.

## 3. Output Qualities

A good handbook page produced by the platform must:

* use clear English for a non-technical SME owner;
* address a concrete business question;
* use reliable and relevant evidence;
* provide traceable sources for important claims;
* clearly distinguish evidence from assumptions;
* contain practical examples relevant to small marketing agencies;
* explain opportunities as well as limitations;
* cover responsible-AI issues when relevant;
* avoid unsupported AI-generated claims;
* explain business implications rather than only describing technology;
* include practical actions, recommendations or decision questions;
* remain concise and easy to scan.

These output qualities correspond directly with the quality criteria defined in the AIBS research proposal.

## 4. Known Constraints

The project has several known constraints.

### Agentic CLI

The team will direct an agentic CLI rather than manually coding the entire system.

The focus is therefore on defining workflows, instructions, inputs, outputs and checks rather than creating complex infrastructure from scratch.

### Existing Wiki and Website

The platform must reuse the existing wiki and course website.

A new content-management system or website will not be developed.

### Non-coder Accessibility

A team member without programming experience must be able to operate the main research workflow.

The system should therefore use simple commands, clear instructions and understandable outputs.

### Human Oversight

The platform assists researchers but does not replace them.

Important decisions such as accepting a source, interpreting interview findings, approving recommendations and publishing handbook content remain human responsibilities.

### Manual Fallbacks

Every automated stage must have a manual fallback.

For example:

* if automatic source retrieval fails, the researcher can paste or upload the content manually;
* if automatic translation fails, translated text can be entered manually;
* if automatic source appraisal is incorrect, the researcher can edit it;
* if evidence extraction fails, the researcher can select evidence manually;
* if page generation fails, the researcher can write or edit the Markdown manually;
* if automatic publishing fails, the final Markdown can be copied into the wiki manually.

## 5. Dutch-Language Source Handling

Support for Dutch-language research is a core requirement of the platform.

Important information about Dutch SMEs may come from sources such as CBS, KVK, sector organisations, regional media and company websites.

The company interview may also be partly or completely in Dutch.

The platform must therefore:

1. automatically identify whether material is Dutch or English;
2. retain the original Dutch text;
3. create an English translation or working summary;
4. keep translated information linked to the original source;
5. clearly indicate that content has been translated;
6. allow the researcher to compare important translated claims with the original;
7. evaluate the reliability of the original source rather than treating the translation as a new source;
8. process Dutch interview transcripts or notes using the same workflow.

This ensures that every team member can research Dutch sources even if they do not speak Dutch.

Translation should support access to evidence, but important claims should remain traceable to their Dutch originals.

## 6. Out of Scope, for Now

The first version will deliberately not include:

* a completely new website or CMS;
* fully autonomous research without human review;
* automatic publication without approval;
* training our own AI model;
* advanced custom machine-learning models;
* real-time monitoring of every AI development;
* automatic implementation of AI inside the selected SME;
* direct integration with the SME's confidential business systems;
* a commercial customer-facing AI chatbot;
* support for every language;
* advanced user accounts and permissions.

The first version focuses on creating a reliable research-to-publication workflow.

## 7. Open Questions and Assumptions

### Assumptions

We currently assume that:

* small marketing agencies can benefit from some forms of generative AI;
* useful regional and sector-specific information can be found in Dutch and English;
* the existing wiki can accept the output generated by the platform;
* researchers will review every page before publication;
* Markdown will be a suitable working format;
* the SME visit will provide useful internal information that cannot be obtained from desk research alone.

## 8. Architectural Blueprint and Build Plan

This section outlines the technical approach and phased execution plan to build the research platform using an agentic CLI[cite: 2].

### Architectural Blueprint
The system relies on a modular pipeline managed by an agentic CLI, passing data through sequential automated stages with built-in human intervention points[cite: 2]. 
* **Input Layer:** Handles ingestion of URLs, PDFs, and transcripts[cite: 2].
* **Processing Layer:** Manages language identification and creates English translations or working summaries of Dutch texts while preserving the original source[cite: 2].
* **Analysis Layer:** Appraises sources (authority, relevance, recency, bias) and extracts claims or statistics connected to specific research questions[cite: 2].
* **Output Layer:** Generates English Markdown drafts and pushes approved pages to the existing course wiki[cite: 2].

### Phased Build Plan

| Phase & Focus | Key Tasks & Sub-Tasks | Deployment / Checkpoint |
| :--- | :--- | :--- |
| **Phase 1: Foundation** | 1. Select and configure the agentic CLI environment.<br>2. Set up manual fallbacks for data entry[cite: 2].<br>3. Connect output pipeline to the existing wiki[cite: 2]. | **Deployment:** CLI successfully authenticates and can push a manual Markdown page to the wiki. |
| **Phase 2: Ingestion & Translation** | 1. Build document/URL ingestion.<br>2. Implement language detection[cite: 2].<br>3. Integrate translation API to process Dutch sources into English summaries[cite: 2]. | **Checkpoint:** System can ingest a Dutch regional article and output an English summary linked to the original[cite: 2]. |
| **Phase 3: Extraction & Drafting** | 1. Prompt engineering for source appraisal (bias, authority)[cite: 2].<br>2. Build evidence extraction linked to external/internal research questions[cite: 2].<br>3. Generate first handbook-page draft[cite: 2]. | **Checkpoint:** System turns a translated interview transcript into a structured draft addressing responsible AI. |
| **Phase 4: Review & Finalization** | 1. Build human-in-the-loop review interface/prompts[cite: 2].<br>2. Implement automated pre-publication checks (clarity, missing citations)[cite: 2].<br>3. End-to-end testing by a non-coder[cite: 2]. | **Deployment:** Full pipeline is operational; team publishes the first official handbook page[cite: 2]. |

### Open Questions

The team still needs to determine:

* which agentic CLI will be used for the final workflow;
* how sources will be stored and referenced;
* how source reliability should be scored;
* how interview recordings and transcripts will be handled;
* how much translation should be automated;
* what exact page format the existing wiki requires;
* how citations will be generated and checked;
* which parts of the workflow should be automated first;
* which marketing agency will participate in the SME visit;
* and how the team will test whether the platform is easy enough for a non-coder to use.

These questions will be refined as the project develops and as the team receives feedback from the SME visit and peer review.
