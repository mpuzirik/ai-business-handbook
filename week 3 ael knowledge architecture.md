# AEL Knowledge Architecture

## 1. What the Platform Has to Know

Our platform supports the research team in producing evidence-based handbook pages for small marketing and advertising agencies in the Netherlands. To do this reliably, the platform needs to understand the project context, have access to reliable research sources, preserve information about the quality of those sources, and keep generated drafts separate from verified evidence.

The first type of knowledge is the **project context**. Before starting a research or writing task, the platform should read a context file containing the target audience, research questions, purpose of the handbook, source-quality criteria, responsible-AI requirements and the scope of the project. This provides a consistent foundation for every weekly handbook page and prevents the platform from treating each task as an unrelated request.

The second type is the **original research material**. This includes reports, academic research, government and institutional publications, webpages, statistics and approved field-research material. Because our research includes both Dutch and English sources, the original language must also be recorded. Each source should retain basic metadata including its title, author or organisation, publication date, URL and date accessed.

Sources should not automatically become evidence simply because they have been collected. The platform therefore also needs the **source appraisal** created during the research process. The appraisal records whether a source is authoritative, relevant, recent and transparent, as well as its possible biases and limitations.

The most important knowledge unit in the architecture is the **evidence record**. Instead of giving the drafting system an entire collection of documents and asking it to produce an answer, useful findings are stored together with the passages that support them. An evidence record connects a claim to its original passage, source, publication information, language, translation where necessary, appraisal and known limitations. This allows a researcher to trace a statement in a handbook draft back to the evidence behind it.

Finally, the platform needs access to previous drafts and approved handbook pages. Draft material and published material are stored separately. This is important because an AI-generated draft is not evidence and should never later be treated as if it were an original research source.

---

## 2. Where the Knowledge Lives and How It Is Found Again

For the first version of the platform, we chose a **structured file-based knowledge repository with evidence retrieval at the time a handbook page is created**.

The information will be separated into project context, original sources, source appraisals, evidence records, protected field research, anonymised field research, handbook drafts and published pages. This structure is deliberately simple because our PRD requires the platform to remain understandable and usable by team members without advanced technical knowledge.

The retrieval process begins with the research question. The platform first reads the project context so that it understands the audience and quality requirements. It then searches the appraised evidence for information relevant to the question. Relevant passages are retrieved together with their source information, appraisal and limitations. Only this selected evidence is passed to the drafting stage.

The workflow can therefore be represented as:

```text id="e4c6ad"
Research Question
        ↓
Project Context
        ↓
Appraised Evidence
        ↓
Relevant Original Passages
        ↓
Draft Handbook Section
        ↓
Evidence and Citation Check
        ↓
Human Review
        ↓
Published Page
```

For example, if the platform is asked whether a marketing agency should enter confidential client information into an AI service, it should retrieve evidence about data protection, confidentiality and vendor data-handling practices. The model should not answer this question only from its general training knowledge.

The connection between research and drafting is an **evidence record**. Each record has a consistent structure containing an evidence ID, topic, claim, original passage, source title, author or organisation, publication date, URL, original language, translation where required, source appraisal and limitations.

This fixed structure acts as a contract between different parts of the platform. The drafting component knows what information it should receive, while the research component knows what information it must preserve.

---

## 3. Why We Chose This Architecture

We chose retrieval of appraised evidence at the time of writing rather than relying only on summaries generated in advance. This decision directly supports a central promise in our PRD: important claims in the handbook should remain traceable to their original sources.

Retrieving the original supporting passage together with its source information makes it possible for the team to check whether the generated statement accurately represents the evidence. It also makes disagreements between sources more visible instead of hiding them inside a combined summary.

We considered **pre-generated source summaries** as an alternative. This approach could make the system simpler because every original document could first be reduced to a shorter summary. However, summarisation can remove qualifications, methodology and context. It would also introduce another layer of AI interpretation between the original evidence and the final handbook page.

For this reason, summaries may still be useful for navigation, but they will not replace the original evidence records.

The current file-based approach is appropriate for the relatively small amount of research produced during this project. If the collection becomes significantly larger and retrieval becomes unreliable or difficult to maintain, we would consider moving the evidence records to a searchable database or index. The requirement to preserve traceability to the original evidence would remain the same.

---

## 4. The Safety Boundary

The safety boundary established in our Technical Blueprint remains unchanged:

> **Raw interview recordings, consent documents, identifiable or unredacted transcripts, and confidential client or company information must not be sent to an external AI model service. Only reviewed, anonymised material may enter the AI-assisted workflow.**

Protected field-research material is stored separately from the information available to the AI-assisted platform. This includes raw recordings, consent documentation, identifiable transcripts and personal information.

Before field-research findings can enter the AI-assisted workflow, a team member must review and anonymise them. Only the reviewed and anonymised notes can then become research evidence.

The boundary can be represented as:

```text id="bfxtsn"
Raw Interview / Consent / Identifiable Information
                    ↓
             Protected Storage
                    X
                    X  MUST NOT CROSS
                    X
════════════════ SAFETY BOUNDARY ════════════════
                    ↓
          Reviewed Anonymised Notes
                    ↓
             Evidence Records
                    ↓
             AI-Assisted Platform
                    ↓
              Human Review
```

This separation reduces the risk that an automated process accidentally reads identifiable interview information and sends it to an external model provider. It also follows the principle that an AI system should receive only the information necessary to perform its task.

---

## 5. Socratic Tutor Questions and Open Issues

The Socratic tutor sent five questions on the Week 2 blueprint. Each is answered in blueprint Rev 4; in short:

| Tutor question | What we changed |
|---|---|
| 1. Where does the scoring rubric live, and which five criteria does it use? | Changed: one rubric, v1.0 in search strategy section 1.1 (Authority, Evidence, Recency, Relevance, Independence and bias); blueprint and platform read that same file |
| 2. How can a Dutch source be appraised before it is translated? | Changed: the order is now Ingest, privacy check, translate if required, then appraise |
| 3. How are government and state-funded sources treated? | Changed: every source type is checked for interests; authority no longer means independence |
| 4. How will E3 (European alternatives) be searched directly? | Changed: product-level searches added; those sources use the same appraisal |
| 5. Where are the Dutch, regional and sector-specific searches? | Changed: KVK, Oost NL, provincial and Dutch sector sources added, with the same translation and appraisal |

The tutor's questions on this knowledge architecture itself are not in this document set. They belong in a section of the build plan, which does not have it yet.

There are still several questions that we need to test during development. In particular, we need to determine how accurately the platform can retrieve evidence as the research collection grows, how Dutch translations should be checked against the original text, and how the system should handle situations where two reliable sources disagree.

We also need to decide how much source appraisal can safely be automated. AI may help identify information such as publication dates, organisations and possible limitations, but the final decision about whether a source is suitable evidence should remain with the research team.

Another issue is preventing generated material from becoming circular evidence. A handbook draft or AI-generated interpretation should never be added to the evidence collection as though it were an original source. Maintaining the separation between sources, evidence and generated content will therefore be tested as the platform develops.

---

## 6. What the Platform Implements, and the LLM Wiki (added in v1.1)

In week 5 the team adopted the course's LLM wiki template (`ael-llm-wiki` on GitHub, set up by Maksim). Knowledge now lives in two places (decision T-011):

| Architecture | Platform and wiki | Decision |
|---|---|---|
| Original sources | The run keeps the unchanged source text on the researcher's computer. Approved sources are copied once into the wiki's `raw/` folder and never edited there | T-011 |
| Source appraisal and evidence records | Each run is one `run.json`: source record, AI scores next to the researcher's decisions, evidence items with verbatim quotes. "Send to Wiki" writes a run page and a source page to the wiki | T-011, T-016 |
| Drafts and published pages kept apart from evidence | Holds: the approved handbook page goes to its own wiki page and is never offered as a source | T-001 |
| Drafting retrieves evidence from many sources | One run is one source (T-010). Across sources, the `/wiki` command answers a question from the wiki only, with a citation after every claim | T-010, T-016 |
| Quotes are traceable | The platform checks quotes and figures against the source; the wiki check compares every quote word for word with its raw file on every push (GitHub Action) | T-016 |
| Protected and anonymised field research | Restricted material (identifiable transcripts, recordings, confidential information) is refused at intake and never stored. Research notes and interview material are never sent to the wiki (tested) | T-002 |
| Published pages | The wiki holds the approved pages; publishing on the course site stays a manual step | T-009 |

**Open (raised by Maksim):** evidence and handbook pages are now stored twice, in the run on the researcher's computer and in the wiki. Which copy is leading has not been decided.

# Decision Log

The full log is the team decision log (T-001 to T-019). Its first entry was made with this document:

## T-001: Evidence Retrieval Architecture

**Date:** 25 September 2026

**Decision:** We decided to use structured evidence records and retrieve relevant original evidence when a handbook section is created. The platform will not rely only on pre-generated summaries or the AI model's general knowledge.

**Problem identified:** Our Week 2 research showed that AI-generated answers can sound equally confident while using conflicting statistics, definitions and interpretations. If our own platform relied mainly on AI-generated summaries, the connection between a handbook claim and its original evidence could become equally unclear.

**What we changed:** We made the evidence record the central connection between research and drafting. An important finding now remains connected to its supporting passage, source information, appraisal, language information and limitations.

**Alternative considered:** We considered summarising every source in advance and using these summaries as the main knowledge base. We decided against this because summaries can remove context and introduce another layer of interpretation between the original source and the final handbook claim.

**Connection to the PRD:** This architecture supports our requirements for reliable evidence, traceable sources, Dutch-language processing and human oversight.

**When we would reconsider:** If the research collection becomes too large for reliable file-based retrieval, we would move the evidence records to a searchable index or database while keeping the same links to the original evidence.
