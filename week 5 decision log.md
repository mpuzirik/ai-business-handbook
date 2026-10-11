# AEL Decision Log — Weeks 3–5

## Purpose

This Decision Log records the important decisions made during the development of our AI-assisted research platform. It explains the problems we identified, the alternatives we considered, what we decided to change and how these decisions relate to our PRD.

Our platform supports the creation of evidence-based AI handbook pages for small marketing and advertising agencies in the Netherlands.

## Decision 001 — Knowledge Retrieval Architecture

**Week:** 3

**Problem identified:** During our research, we noticed that AI-generated articles could present confident conclusions based on different statistics and interpretations. Relying only on AI-generated summaries could make it difficult to trace information back to original sources.

**Decision:** We chose an evidence-retrieval approach. The platform should retrieve relevant passages from appraised sources and preserve their original references.

**Alternative considered:** Using pre-generated summaries as the main knowledge base.

**Reason:** Summaries may remove important context or qualifications. Original evidence records provide better traceability and allow researchers to verify important claims.

**PRD connection:** Source reliability, evidence traceability and human oversight.

**Status:** Architecture decision documented.

## Decision 002 — Protection of Field Research Data

**Week:** 3

**Problem identified:** SME interviews may contain confidential company information or personal data that should not be shared with external AI services.

**Decision:** Raw interview recordings, consent documents and identifiable information must remain in protected storage. Only reviewed and anonymised information may enter the AI-assisted research workflow.

**Reason:** This reduces privacy risks and supports responsible handling of field-research information.

**PRD connection:** Responsible AI, data protection and human oversight.

**Status:** Safety boundary documented. Technical enforcement requires verification.

## Decision 003 — First Working Version of the Research Tool

**Week:** 4

**Problem identified:** Our initial documents described how the research platform should work, but we needed a working version to demonstrate whether the proposed approach was practical.

**Decision:** The team developed a first working version (V0) of the desk research tool and demonstrated it to the lecturers.

**Reason:** Building V0 allows us to evaluate the research workflow in practice rather than relying only on the PRD and architecture documents.

**PRD connection:** Research automation, source processing and handbook production.

**Status:** V0 built and demonstrated.

**Evaluation still required:** Record which functions were demonstrated successfully, which limitations were identified and what changes followed the lecturer feedback.

## Decision 004 — Improving the SME Knowledge Gaps Page

**Week:** 5

**Problem identified:** Our initial handbook page described several possible AI knowledge gaps but did not clearly distinguish general research findings from assumptions about individual marketing agencies.

**Decision:** We revised the page to separate established research findings from questions that still require field research.

We also introduced preliminary priorities for business value, confidentiality, reliability, employee skills and implementation costs.

**Reason:** The handbook should not present assumptions about an SME as confirmed findings. It should help the owner identify which questions need to be answered before adopting AI.

**PRD connection:** Accuracy, relevance to the target audience, evidence quality and practical usefulness.

**Status:** Revised draft prepared; publication confirmation pending.

## Decision 005 — Selecting AI-Assisted Content Creation as a Use Case

**Week:** 5

**Problem identified:** Small marketing agencies have several potential AI applications, but discussing all of them would make it difficult to provide a specific and measurable recommendation.

**Decision:** We selected AI-assisted social media content creation as the focus of the Week 5 AI Use Cases handbook page.

**Alternative considered:** Covering multiple AI applications, including customer communication, campaign analysis and automated marketing workflows.

**Reason:** Content creation is directly relevant to marketing agencies and allows us to propose a small, controlled pilot. It can be evaluated through drafting time, editing effort, content quality, costs and employee experience.

**PRD connection:** SME relevance, practical recommendations and evidence-based decision-making.

**Status:** Full handbook draft prepared; final review and publication confirmation pending.

## Decision 006 — Human Approval Before Publishing AI Content

**Week:** 5

**Problem identified:** AI-generated marketing content may contain inaccurate information, generic messaging or content that does not match the client's brand.

**Decision:** We recommend that AI supports drafting while employees remain responsible for reviewing and approving client-facing material.

**Reason:** Human review helps maintain accuracy, originality, brand consistency and client trust.

**PRD connection:** Responsible AI, accuracy, human oversight and output quality.

**Status:** Recommendation included in the Week 5 handbook draft.

## Decision 007 — First Evaluation of V0

**Week:** 5

**Problem identified:** Demonstrating that the research tool works is not enough to establish that it meets all PRD requirements.

**Decision:** Evaluate V0 against source appraisal, evidence traceability, Dutch-to-English processing, draft generation, responsible-AI coverage, human review and manual fallback requirements.

**Reason:** Testing against predefined requirements allows the team to identify actual strengths, failures and improvements.

**PRD connection:** All major functional and quality requirements.

**Status:** Evaluation planned; results not yet recorded.
