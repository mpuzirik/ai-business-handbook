# AEL Technical Blueprint — Revision 4

*Revised after Week 2 Socratic feedback. This version aligns the platform with the source-appraisal rubric in `week 2 search strategy.md`, version 1.0.*

---

## The Production Line

```text
 [context file: SME, research questions, quality criteria, scope]
                         |
                         v
 +--------+   +--------------------+   +----------------------+   +---------------+
 | Ingest |-->| Eligibility /      |-->| Translate if needed  |-->| Human Appraise|
 +--------+   | Privacy Check      |   +----------------------+   +---------------+
              +--------------------+                                  |
                                                                      v
                                                              +----------------+
                                                              | Extract        |
                                                              | Evidence       |
                                                              +----------------+
                                                                      |
                                                                      v
                                                                  +-------+
                                                                  | Draft |
                                                                  +-------+
                                                                      |
                                                                      v
                                                                  +-------+
                                                                  | Check |
                                                                  +-------+
                                                                      |
                                                                      v
                                                                  Publish

# The Six Decisions

## 1. What roles own the stages?

| Stage | What happens | Owner |
|---|---|---|
| Ingest | Saves the source and basic information about it. | Developer |
| Eligibility / Privacy Check | Checks whether the source is allowed into the platform and records its language. | Researcher + Developer |
| Translate if required | Creates an English working translation when the reviewer cannot understand Dutch. The original is kept. | Developer |
| Human Appraise | A researcher scores the source using rubric version 1.0 from `week 2 search strategy.md`. | Researcher |
| Extract Evidence | Extracts useful claims and connects them to a source and research question. | Developer |
| Draft | Creates a handbook draft from approved evidence. | Developer |
| Check | Checks citations and quality before publication. | Tester |
| Publish | Publishes only after human approval. | Deployer |

The Product Manager owns the PRD and quality criteria used across the whole workflow.

## 2. Who decides what happens next?

The platform does not make final research decisions by itself.

- After **Ingest**, the source must pass the eligibility and privacy check.
- If the source is Dutch and the reviewer cannot understand Dutch, it is translated before full appraisal.
- After **Human Appraise**, the researcher decides whether the source can be used.
- Only approved evidence can move to Draft.
- Publish is blocked until the Tester has completed the final human review.

The script may calculate scores, but the human researcher makes the final decision.

## 3. The source-record contract

Each source has one source record.

It contains:

- source ID;
- title;
- author or organisation;
- URL or file reference;
- publication date;
- retrieval date;
- source type;
- original language;
- whether translation was required;
- reference to the original;
- reference to the translation, if used.

The appraisal uses **rubric version 1.0 from `week 2 search strategy.md`**.

The five scored criteria are:

1. Authority;
2. Evidence;
3. Recency;
4. Relevance;
5. Independence and bias.

Each criterion receives 0, 1 or 2 points.

The record also stores:

- the five scores;
- total score;
- provisional tier;
- reason for the scores;
- reviewer;
- review date.

The following four checks are also recorded:

- Transparency;
- Comparability;
- Traceability;
- Cross-checking.

Every extracted claim must remain linked to its original source.

## 4. Where shared context lives

One context file is read by the relevant stages.

It contains:

- target SME;
- research questions;
- handbook quality criteria;
- source-appraisal rubric reference;
- privacy rules;
- project scope;
- handbook style.

The full scoring rubric is not copied into every stage.

The official rubric is stored in:

`week 2 search strategy.md` — Section 1.1, rubric version 1.0.

## 5. The line nothing may cross

Raw interview recordings, unredacted transcripts and confidential company information must not be sent to an external AI model service.

The Eligibility / Privacy Check happens before translation or other model-assisted processing.

Translation does not create an exception to this rule.

Only material that follows the agreed consent, anonymisation and privacy process may enter the model-assisted workflow.

## 6. Two readers, not one

The Check stage has two parts.

### Automated checks

The platform checks:

- whether claims have source references;
- whether the source record exists;
- whether appraisal is complete;
- whether required information is missing.

These checks confirm structure and traceability. They do not prove that a claim is true.

### Human Tester review

The Tester checks:

- whether the source actually supports the claim;
- factual accuracy;
- clarity;
- misleading comparisons;
- responsible-AI issues;
- usefulness to the SME owner;
- whether limitations are explained honestly.

Nothing is published until the human review is complete.

# Trace to the PRD

| PRD promise | Where it appears |
|---|---|
| Add and identify sources | Ingest |
| Protect restricted information | Eligibility / Privacy Check |
| Translate Dutch sources when required | Translate |
| Appraise source quality | Human Appraise |
| Keep evidence linked to its source | Extract Evidence |
| Draft using approved evidence | Draft |
| Check citations and quality | Check |
| Require human approval | Check + Publish |

# Changes After Socratic Feedback

## Question 1

The appraisal stage now uses the same rubric as Assignment 2:

`week 2 search strategy.md`, Section 1.1, rubric version 1.0.

The five scored criteria are Authority, Evidence, Recency, Relevance and Independence and bias.

## Question 2

The old workflow was:

**Ingest → Appraise → Translate**

The new workflow is:

**Ingest → Eligibility / Privacy Check → Translate if required → Human Appraise**

This means a reviewer does not have to judge evidence in a language they cannot understand.

## Question 3

Bias is no longer limited to commercial companies.

Government, state-funded, academic and industry sources are also checked for relevant interests and possible bias.

Authority does not automatically mean independence.

## Question 4

The platform now supports the E3 product-level research into specific European AI providers and products.

These sources use the same appraisal process as the other research sources.

## Question 5

The platform also supports Dutch-language, regional and sector-specific sources such as KVK, Dutch marketing-sector organisations, Oost NL and provincial sources.

These sources follow the same translation and appraisal process as English-language sources.
