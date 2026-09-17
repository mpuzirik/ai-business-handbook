# AEL Technical Blueprint, Revision 3

---

**The production line**

```
 [context file: SME, AIBS §4 quality criteria, scope]
                    |
                    v
  +--------+   +----------+   +-----------+   +---------+   +-------+   +---------+
  | Ingest |-->| Appraise |-->| Translate |-->| Extract |-->| Draft |-->| Check   |--> Publish
  +--------+   +----------+   +-----------+   |Evidence |   +-------+   +---------+
                                               +---------+
```

**The company** (the four build roles, and what each is accountable for):

```
  Product Manager: guards the criteria every stage is judged against; owns the PRD; not tied to one box
  Developer:        builds and maintains Ingest, Translate, Extract Evidence, Draft
  Tester:           holds the bar at Check — says when a page doesn't clear it
  Deployer:         Publish, and makes sure someone else could re-run what was done
```

## The Six Decisions

**1. What roles that own stages.** A part is a stage on the production line. Each stage is built and owned by one of the four AEL roles.

| Stage | What happens | Built/owns it (AEL role) |
|---|---|---|
| Ingest | Fetch a source, save a fixed snapshot, record where it came from | Developer |
| Appraise | Score reliability by hand against a fixed rubric; a script does the arithmetic | Developer (built the scoring script) |
| Translate | Produce an English working summary of a Dutch source, original kept alongside it | Developer |
| Extract Evidence | Pull individual claims out and tag each to a research question | Developer |
| Draft | Assemble a page from evidence that has passed Appraise only | Developer |
| Check | Confirm every claim in the draft is tagged to a real, appraised source, and hold it against the quality bar | Tester |
| Publish | Sign the page off and push it to the wiki | Deployer |

The Product Manager doesn't own a box in this table as their job is owning the PRD and the quality criteria the whole pipeline is judged against, which sits above the pipeline rather than inside one stage of it.

**2. Who decides what happens next**

**3. The one named seam and its contract.** One file per source, created by Ingest and completed by Appraise: an identifier and title; where it came from, when published, when retrieved; the original language; a fingerprint of the exact snapshot read, so appraisal can be checked against what was actually fetched; once appraised, the five scores, the resulting tier, and who scored it; an English working summary in the researcher's own words; and a short list of extracted claims, each pointing to a research question. No later stage may use a source whose record is incomplete.

**4. Where shared context lives? One context file every part reads.** Target SME (10–50 FTE marketing/creative agencies, NL), the quality criteria from the AIBS proposal §4, what is out of scope, and house style live in one file every stage reads before it runs. Nothing is duplicated into a stage's own instructions, because that is exactly how six pages stop agreeing with each other.

**5. The line.** Raw interview recordings and unredacted transcripts never reach a model service. The material never enters the platform at all. A person redacts by hand, outside the repository, into a thematic note and it is then allowed anywhere in a model.

**6. Two readers, not one.** A checking part reads the draft first, but it can only test attribution, not truth. The Tester reads it second, against the remaining AIBS §4 criteria a script cannot judge wording, factual accuracy, responsible-AI completeness, usefulness to the owner. Publish is blocked until both have passed. Nothing is left as "nothing yet" here, because the PRD requires human approval before every page regardless.

---

## Trace to the PRD

| PRD promise | Lands in | Departure? |
|---|---|---|
| Add source material; capture title, author, date, type, language | Ingest, source record | none |
| Translate Dutch sources, keep original, claims traceable | Translate | none |
| Appraise on authority, relevance, recency, evidence quality, **bias** | Appraise | **Departure.** "Bias" narrows to *independence* (commercial interest only); broader bias stays a judgement call, not a scored dimension, since it isn't consistently scoreable the way commercial interest is. |
| Extract and organise evidence, linked to source and question | Extract Evidence | none |
| Generate first draft from selected evidence only | Draft | none |
| Check draft for unsupported claims, weak citations, unclear wording, factual inconsistencies, missing responsible-AI content, usefulness to owner | Check + Tester review | **Departure.** Script checks only the first two (attribution); the other four move to the Tester's read in Decision 6, because a script cannot judge truth or usefulness. |
| Human review and approval; no auto-publish | Publish | none |
| Non-coder accessible workflow | cross-cutting | none |
| Interview/confidential material off any external AI service | The line (Decision 5) | none |
