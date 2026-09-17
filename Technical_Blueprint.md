# AEL Technical Blueprint, Revision 1

**Project:** Evidence-Based AI Adoption Handbook for Small Marketing and Advertising Agencies (10 to 50 FTE)
**Document:** Technical architecture, tooling, scoring logic and confidential data handling
**Owner:** Deployer, with Developer
**Reference documents:** AEL PRD (draft 2), AIBS Research Proposal (revision 2)

---

## 0. Corrections in This Revision

Recorded here because the portfolio asks what changed and why.

| # | Problem in revision 2 | Fix |
|---|---|---|
| 1 | Worked example of the scoring engine miscalculated (3.65 instead of 3.70) | Corrected; every figure in this document is now computed, not typed |
| 2 | Matrix 2 double-counted data safety: 25% of the weight and a veto | Data safety is a gate only, removed from the weighted sum, weights redistributed |
| 3 | Matrix 1 gates would have barred the proposal's own comparable-agency examples | Claim classes added: an illustrative case needs a lower tier than a sector-wide number |
| 4 | Source files held full original text, a copyright problem in a pushed repo | Quoted extracts capped, own-words summary, full text kept in a local snapshot store |
| 5 | `sha256` was described over a live URL, which changes on every fetch | Hash is taken over the saved snapshot file |
| 6 | Pre-commit hook would have run on nobody's machine | `make doctor` sets `core.hooksPath` and fails if unset |
| 7 | Quality lint claimed 12 automated checks | 4 script checks, 8 printed review prompts for a human |
| 8 | Redaction lint presented as the control, but the deny-list is local to one machine | Lint demoted to one layer; named human identifiability review added |
| 9 | Productivity target confounded time saving with practice effect | Control source per researcher per week, and human minutes are self-logged, not inferred |
| 10 | Week 2 carried the whole pipeline plus the baseline exercise | `score.py` moved to phase 2, scoring done by hand in week 2 |

---

## 1. Purpose and Design Principles

The AEL platform supports the research team in ingesting, translating, appraising, tagging and drafting evidence into weekly handbook pages. It does not replace researcher judgement.

1. **Human in the loop at the gates.** Automation moves and reshapes text. Humans decide what is true, what is reliable and what gets published.
2. **Deterministic checks are never done by a model.** Arithmetic, tag resolution, gate enforcement and redaction linting run as plain scripts. Only translation, summarising, evidence extraction and draft assembly use the agent.
3. **Everything citable lives in Git.** Evidence, scores and drafts are plain text under version control. No database.
4. **Confidential field material never enters the repository or the agent working directory.** Enforcement is layered, not trust-based.
5. **The platform must be operable by a non-coder.** One-line commands, no code editing.
6. **No control is claimed that is not actually enforced.** Where a check is procedural rather than technical, this document says so.

---

## 2. System Overview

```
 PUBLIC / DESK RESEARCH
 NL and EN sources: CBS, KVK, Oost NL, EU Commission, Draghi, academic, trade press
 |
 v
 [1] make ingest ........... agent: fetch, snapshot, classify, extract metadata
 |
 v
 [2] make translate ........ agent: EN working summary, capped quoted extracts
 |
 v
 [3] make score ............ human: five dimension scores | script: math and tier
 |
 v
 [4] make evidence ......... agent: extract claims, map to E1-E6 / I1-I6
 |
 v
 EVIDENCE VAULT (/evidence, Markdown + YAML)
 |
 +---- redacted fieldwork notes (section 7)
 |
 v
 [5] make draft ............ agent: assemble page from approved evidence only
 |
 v
 [6] make check ............ script: tag audit, claim-class audit, structural lint
 |
=========================== HUMAN APPROVAL GATE ================================
 |
 v
 [7] team editorial review, 8 printed review prompts signed off
 |
 v
 [8] make publish .......... Deployer: push to GitHub wiki / course web
```

Steps 1, 2, 4 and 5 are agent steps. Step 3 is a human judgement with script arithmetic. Step 6 is script only. Steps 7 and 8 are human only.

---

## 3. Repository Structure

```
ael-handbook/
  README.md                  what this is, and the five commands you actually need
  CHANGELOG.md               in-progress and done entries per work item
  CLAUDE.md                  standing rules the agent must follow in this repo
  Makefile                   the whole command surface for the team
  .gitignore                 blocks any path that could carry raw or full-text material
  .githooks/pre-commit       redaction lint and tag audit, activated by make doctor

  docs/
    prd.md  research-proposal.md  blueprint.md  user-guide.md
    decisions/ADR-001-cli-choice.md

  evidence/
    sources/SRC-2026-001.md    one file per desk source, YAML + own-words summary
    snapshots/                 LOCAL ONLY, gitignored: full fetched source files
    tools/TOOL-001.md          per tool: provider, hosting, DPA, training use, exit cost
    fieldwork/FW-001.md        redacted thematic notes only, never transcripts
    index.md                   generated table of sources, tiers and claim permissions

  matrices/
    source-rubric.yaml  usecase-rubric.yaml  scores/UC-001.yaml

  drafts/         published/
  scripts/
    score.py  check_claims.py  redaction_lint.py  build_index.py  timelog.py
  templates/
    source.md  fieldwork.md  page.md  usecase.yaml
  logs/runs/  logs/time/
```

Confidential field material lives at `~/ael-confidential/`, outside this tree. Section 7.

---

## 4. Agentic CLI Layer

### 4.1 Tool selection

**Selected:** one agentic CLI (Claude Code) running inside the repository, wrapped by `make` targets, with repository rules in `CLAUDE.md`.

| Rejected option | Why not |
|---|---|
| Web chat interface | No filesystem write, no repeatable runs, no logs; copy-paste breaks traceability |
| Custom LangChain or LiteLLM agent | Real development work, one developer, four weeks |
| Scripts only, no agent | Cannot read a Dutch PDF and produce a usable working summary |
| Two agents in parallel | Two sets of behaviour to document and test, no added capability |

**Capabilities that made an agentic CLI necessary**, rather than a script or a chat window: multi-step file work in one instruction; tool use in sequence (fetch, read, write structured YAML); repeatability of artefact shape week to week; run logs that can be cited in the portfolio; and parameterised commands, so no team member edits code.

**Open dependency:** every team member who runs the pipeline needs the CLI installed and access to a model. Confirm licence cost and who provides it before phase 2, otherwise the usability test cannot run.

### 4.2 Command surface

| Command | Does what | Who or what executes |
|---|---|---|
| `make doctor` | Environment, keys, `core.hooksPath`, deny-list, stray C3 files | script |
| `make ingest URL="https://..."` | Fetch, save snapshot, hash it, create `SRC-` file | agent |
| `make ingest FILE="~/Downloads/kvk.pdf"` | Same, from a local public PDF | agent |
| `make translate ID=SRC-2026-014` | EN working summary, extracts capped at 25 words | agent |
| `make score ID=SRC-2026-014` | Asks the five scores, computes total and tier | human + script |
| `make evidence ID=SRC-2026-014 Q=E2` | Extracts claims as EVID nodes, tagged to a sub-question | agent |
| `make tools NAME="ChatGPT Team"` | Creates or updates a tool jurisdiction dossier | agent |
| `make fieldwork ID=FW-001` | Redacted note from template, then lint and reviewer field | human + script |
| `make matrix UC=UC-001` | Applies the safety gate, then the weighted score | script |
| `make draft PAGE=E2-vendor-dependency` | Assembles a page from approved evidence only | agent |
| `make check PAGE=E2-vendor-dependency` | Tag audit, claim-class audit, structural lint, review prompts | script |
| `make log-time TASK=score ID=SRC-2026-014 MIN=12` | Records human minutes for section 9 | human + script |
| `make publish PAGE=E2-vendor-dependency` | Copy to `published/`, push to wiki | script |

### 4.3 Worked examples

**Ingest a Dutch institutional report**

```bash
$ make ingest URL="https://www.kvk.nl/example-digitalisering-mkb"

[ingest] fetching ......................... ok (text/html, 14.2 kB)
[ingest] snapshot saved ................... evidence/snapshots/SRC-2026-014.html (gitignored)
[ingest] sha256 of snapshot ............... 9f2c1e...  (committed in the SRC file)
[ingest] language detected ................ nl
[ingest] metadata: KVK, 2025-11-14, institutional_report, claim_domain: market
[ingest] created evidence/sources/SRC-2026-014.md  status: needs_appraisal
[ingest] next: make translate ID=SRC-2026-014
```

**Score it**

```bash
$ make score ID=SRC-2026-014

Authority      (25%) [1-5]: 4
Relevance      (25%) [1-5]: 3
Evidence rigor (20%) [1-5]: 3
Recency        (15%) [1-5]: 5
Independence   (15%) [1-5]: 4

weighted total = 3.70 / 5.00
tier = SUPPORTING
may carry:  qualitative sector claim, illustrative case, legal or contractual claim
may NOT carry alone:  quantitative sector claim (needs a second independent source)
scored_by required: > anastasia
written to evidence/sources/SRC-2026-014.md
```

**Check a draft**

```bash
$ make check PAGE=E2-vendor-dependency

[check] sentences classified as claims .... 23
[check] resolvable tags ................... 22
[check] FAIL line 41: claim with no SRC-ID
        "Most agencies now run at least one non-EU model in production."
[check] FAIL line 52: tag SRC-2026-099 does not exist
[check] FAIL line 58: claim class 'quantitative_sector' cites one SUPPORTING source
        needs a PRIMARY source or a second independent SUPPORTING source
[check] WARN line 63: claim class 'illustrative_case' not labelled as a single case
[check] structural lint (4 script checks) . 2 of 4 passed
        missing: "Actions for the owner" section, "Limitations" section
[check] counter-evidence field ............ EMPTY, review failure
[check] review prompts for the PM ......... 8 printed to logs/runs/
[check] result: BLOCKED, 4 errors, 2 warnings
```

**Create a redacted fieldwork note**

```bash
$ make fieldwork ID=FW-001

[fieldwork] created evidence/fieldwork/FW-001.md from template
[fieldwork] thematic takeaways only, no transcript text
[fieldwork] deny-list scan .................. FAIL, line 12 matched a listed term
[fieldwork] identifiability_reviewed_by ..... EMPTY
[fieldwork] status: blocked_unredacted, commit will be refused
```

### 4.4 Source file schema

```yaml
---
id: "SRC-2026-014"
title: "Digitalisering in het MKB, creatieve sector"
author_org: "KVK"
url: "https://www.kvk.nl/example-digitalisering-mkb"
publication_date: "2025-11-14"
retrieved: "2026-09-15"
snapshot: "evidence/snapshots/SRC-2026-014.html"   # local, gitignored
snapshot_sha256: "9f2c1e..."                        # committed, proves what was read
original_language: "nl"
source_type: "institutional_report"   # institutional | academic | trade_press | case_report | vendor | blog
claim_domain: "market"                # market | tooling | structural | legal
appraisal_scores:
  authority: 4
  relevance: 3
  evidence_rigor: 3
  recency: 5
  independence: 4
  weighted_total: 3.70
tier: "supporting"
scored_by: "anastasia"
scored_on: "2026-09-15"
status: "approved"
---

## Working summary (en, own words)
...

## Quoted extracts (each under 25 words, page or section noted)
- p.7: "<short quote>"

## Extracted evidence
- EVID-01 (I1): reported time reduction in brief synthesis, figure and page
- EVID-02 (E5): named regional support scheme, eligibility threshold
```

Full original text is **not** committed. It sits in the local snapshot, and the committed hash proves which version was appraised. This keeps traceability without republishing a source in a repository that pushes to a public wiki, which is the same copyright caution the handbook gives agencies.

For Dutch sources the reviewer opens the local snapshot beside the summary to check translation of statistical and legal terms. The named Dutch reader is recorded in `docs/user-guide.md`.

---

## 5. Matrix 1, Source Reliability

### 5.1 Rubric

Score each dimension 1 to 5. Weighted total is on the same 1.00 to 5.00 scale.

| Dimension | Weight | Anchor for 5 | Anchor for 1 |
|---|---|---|---|
| Authority | 25% | Official body, statistics agency, peer-reviewed | Anonymous or undated content marketing |
| Relevance | 25% | Directly about small marketing or creative agencies and one of our sub-questions | General AI commentary, no sector or size link |
| Evidence rigor | 20% | Method and sample described, data or verified pilots | Assertion with no basis given |
| Recency | 15% | Inside the window for its `claim_domain` | Outside it, with no reason to still hold |
| Independence | 15% | No commercial interest in the conclusion | Published by the vendor it recommends |

Recency windows differ by claim domain, since a 2024 structural analysis can still be current while 2024 model pricing is not:

| claim_domain | Window for a 5 | Reason |
|---|---|---|
| tooling | 0 to 9 months | Capability and pricing move quarterly |
| market | 0 to 18 months | Adoption surveys age, but slower |
| legal | currently in force | Only the current instrument counts |
| structural | up to 3 years | Draghi-type competitiveness analysis holds |

Jurisdiction is **not** a scored dimension here. CBS and Draghi have no provider jurisdiction to report and would be penalised for something irrelevant to their reliability. Tool jurisdiction is recorded in `evidence/tools/`, where E2 actually needs it.

### 5.2 Tiers

| Weighted total | Tier |
|---|---|
| 4.00 to 5.00 | primary |
| 3.00 to 3.99 | supporting |
| 2.00 to 2.99 | background |
| below 2.00 | rejected, kept in the vault with a reason, for transparency |

### 5.3 Claim classes, not one blanket gate

Revision 2 required a primary source or two supporting sources for every factual claim. Tested against real material that gate was unworkable: a CBS statistic on SMEs generally scores **4.50** and is primary, but anything specific to 10 to 50 person agencies using generative AI lands around **3.70**, supporting, and a trade-press case study of one agency scores about **3.45**. Under one blanket gate almost nothing in our actual sector could be cited, and the team would quietly override the rule, which is worse than a rule calibrated to reality.

So the permission depends on what the sentence is doing:

| Claim class | Minimum evidence | Page must state |
|---|---|---|
| Quantitative sector claim ("agencies save x hours") | One primary, or two independent supporting | The figure's source and population |
| Qualitative sector claim ("agencies report concern about y") | One supporting | Nothing extra |
| Legal or contractual claim (a DPA term, a statutory duty) | The instrument or the provider's own terms | Which document and which clause |
| Tool data-handling claim | The tool dossier, not press coverage of the tool | Date checked, since terms change |
| Illustrative case ("agency X piloted z and dropped it") | One supporting or background source | That it is a single reported case, not a general effect |
| Our own field finding | An `FW-` note | That it is one company |

This is what lets the research proposal's 2 to 4 comparable-agency cases do their job. They are examples, labelled as examples, and they are never the basis of a number.

**Hard rules the script enforces regardless of score:**

* `source_type: vendor` can never carry a productivity, accuracy or safety claim about its own product. It can carry what the vendor contractually commits to.
* `source_type: case_report` can never carry a quantitative sector claim, whatever it scores.
* A tool data-handling claim older than 90 days is flagged for recheck.

---

## 6. Matrix 2, AI Use-Case Suitability

### 6.1 Structure

Revision 2 gave data safety 25% of the weight **and** a veto. Once a veto fires the arithmetic is irrelevant, so half the weighting was decoration. Safety is now a gate, evaluated first, and removed from the sum.

**Stage 1, safety gate.** A use case is **keep human** if any of these holds, whatever it would score:

* the task requires client-identifiable material and no DPA or equivalent covers the tool;
* the provider's terms permit training on submitted content and cannot be opted out of;
* a client contract or NDA prohibits third-party processing of that material;
* the output would reach a client with no human author taking responsibility for it.

The page must then state the condition that would change the answer, because "not yet" and "never" are different recommendations for an owner.

**Stage 2, weighted score**, for use cases that pass the gate:

`Suitability = (P x 0.45) + (Q x 0.35) + (I x 0.20)`

| Metric | Weight | 1 | 3 | 5 |
|---|---|---|---|---|
| **P** Productivity gain | 45% | Under 1 hour per month across the team | 2 to 6 hours per month | Over 10 hours per month against a recorded baseline |
| **Q** Creative quality retention | 35% | Generic, unusable with a client | Usable as raw input, full rewrite needed | Agency standard with normal editing |
| **I** Implementation effort | 20% | Needs a developer | A day of setup and a written instruction | Usable immediately by a marketer |

| Suitability | Recommendation |
|---|---|
| 3.80 to 5.00 | Pilot now, named owner, measured baseline |
| 3.00 to 3.79 | Conditional hybrid: internal drafts only, final output human authored |
| below 3.00 | Keep human |

No cap on Q is needed now that it carries 35%. A use case with Q at 1 and everything else at 5 scores **3.60**, which lands in conditional hybrid, which is the correct advice: use it internally, do not ship it.

### 6.2 Evidence requirement

Each score carries a reference: a `SRC-ID`, `TOOL-ID` or `FW-ID`. A score with no reference is written `basis: assumption` and the page labels the recommendation untested. Without this the matrix turns group opinion into a number that looks measured.

```yaml
id: "UC-001"
name: "AI summarisation of incoming client briefs"
gate:
  result: "FAIL"
  reason: "briefs contain client-identifiable material, no DPA on the tool tier in use"
  basis: "TOOL-002, FW-001"
  condition_to_revisit: "EU-hosted business tier with signed DPA and training opt-out"
scores:
  P: {value: 4, basis: "FW-001, 3 to 4 briefs per week at about 25 minutes each"}
  Q: {value: 3, basis: "SRC-2026-008, supporting"}
  I: {value: 5, basis: "TOOL-002"}
suitability: 3.85
recommendation: "keep human now; would be a priority pilot once the DPA condition is met"
```

This is the case the structure exists for: the arithmetic says priority pilot at 3.85, the gate says not yet, and the owner gets both plus the one thing that would unlock it.

---

## 7. Confidential Data Boundary

### 7.1 Naming

Revision 2 called this an air gap. It is not one, since the same laptop records the interview and runs the agent. Naming a control that does not exist invites the team to trust it. This is a **confidential data boundary** with three enforcement layers, each with its limits stated.

### 7.2 Data classification

| Class | Examples | Where it may live | May a model see it |
|---|---|---|---|
| C3 confidential | Raw audio, unredacted transcript, client contracts, NDAs, financial figures, client brand assets, the deny-list | `~/ael-confidential/` only, outside the repo | Never, local models included |
| C2 internal | Redacted thematic fieldwork notes, anonymised paraphrase | `evidence/fieldwork/` | Yes, after lint and reviewer sign-off |
| C1 public | Desk sources, snapshots, tool dossiers, drafts | repo (snapshots local) | Yes |

### 7.3 Boundary

```
  ~/ael-confidential/            OUTSIDE the repository and the agent working
    audio/interview-01.m4a       directory, not in any synced cloud folder
    transcripts/raw-01.docx
    deny-list.txt
        |
        |  MANUAL, human only, no agent involvement
        v
  [ redact, paraphrase into thematic takeaways ]
        |
        v
  ael-handbook/evidence/fieldwork/FW-001.md          C2, enters the repo
        |
        +--> deny-list lint (machine, weak)
        +--> identifiability review by a second person (human, the real control)
        |
        v
  pre-commit hook  ->  commit allowed  ->  agent may read it
```

### 7.4 The three layers, and what each cannot do

**Procedural.** Only the interviewer handles C3. Redaction is manual. Raw material is never pasted into any chat window, terminal or editor inside the repository directory. *Limit:* this is discipline, not a mechanism.

**Repository.** `make doctor` sets `git config core.hooksPath .githooks`, since hooks are not shared by `git clone` and without that line the hook runs on nobody's machine. `.gitignore` blocks `*.m4a`, `*.wav`, `raw/`, `transcripts/`, `*-unredacted.*`, `evidence/snapshots/`. The pre-commit hook runs `redaction_lint.py` over `evidence/fieldwork/`. *Limit:* the deny-list is C3 and uncommitted, so it exists only on the interviewer's machine. On anyone else's the lint passes trivially. It also cannot catch identification by description, which is how a small agency's client is actually recognised. Therefore the lint is a backstop, and the named **identifiability review by a second team member** is the control that counts. `FW-` files carry `identifiability_reviewed_by` and the hook refuses an empty field.

**Tooling.** An agentic CLI can read any file inside its working directory, so proximity is the risk rather than intent. The confidential folder therefore sits outside the repository path entirely; `CLAUDE.md` forbids reading or traversing outside the repository and requires refusing a command that points outside it; the agent is always run from the repository root; and `make doctor` fails if any C3 file pattern is found anywhere under the tree.

### 7.5 Consent and retention

Recording requires explicit consent on record, with the purpose stated. Raw audio is deleted once the redacted note is approved, and at the latest at the end of the module. The participant sees what will be published about their company before it is published. This is a GDPR requirement and also the reason an agency agrees to the interview at all.

---

## 8. What the Checks Can and Cannot Do

The module owners asked what content-quality risks come from drafting with an agentic platform. Stated plainly:

| Risk | Automation catches | Only a human catches | Mitigation |
|---|---|---|---|
| Fabricated citation | Tag resolving to no file | Tag resolving to a real file that does not contain the claim | Reviewer spot-checks 3 claims per page against the snapshot, logged in the page frontmatter |
| Claim drift in summarising | Nothing | A hedged finding turned confident | Local snapshot opened beside the summary at review |
| Dutch translation error | Nothing | A mistranslated statistical or legal term | Named Dutch reader checks every NL-sourced number |
| Cherry-picking toward our productivity assumption | Empty `counter_evidence` field | Evidence against the assumption quietly dropped | Empty field is a review failure, not a pass |
| Vendor material as evidence | `vendor` and `case_report` used outside their permission | Vendor claims relayed through trade press | Independence dimension plus 5.3 hard rules |
| False precision in the matrices | Scores with no `basis` | A plausible but unfounded score | `basis: assumption` forces the label on the page |
| Generic prose | Required sections present or absent | Whether it answers an owner's decision | 8 review prompts, PM signs each off |

For the portfolio, in two sentences: the tag audit verifies that a claim is **attributed**, not that it is **true**. Verification of truth stays with the reviewer, which is why phase 3 does not remove the human gate.

---

## 9. Measuring the Productivity Claim

The PRD claims the platform reduces repetitive research and writing work.

**Human minutes are self-reported, not inferred.** Run logs give wall-clock time, which is not the same as researcher effort, so `make log-time` records minutes per task per person into `logs/time/`.

**The practice effect is controlled.** Comparing week 2 manual work against week 4 pipeline work would measure the team getting faster as much as the tool. Therefore each researcher also processes **one control source manually each week**, so the manual figure moves with practice alongside the pipeline figure. The reported saving is pipeline against same-week manual, not against week 2.

| Metric | Baseline | Target | Source |
|---|---|---|---|
| Human minutes per source, ingest to tagged evidence | week 2, two sources per person | minus 40% against same-week control | `logs/time/` |
| Human minutes to first draft of a page | week 2 | minus 30% against same-week control | `logs/time/` |
| Tag coverage of claim sentences | not measured | 100% | `make check` |
| Rework rate at the human gate | not measured | under 25% of drafts blocked twice | check results |
| Claim-class violations per draft | not measured | trending to zero | check results |

Targets are proposals for the team to confirm in week 2. A time saving accompanied by a fall in tag coverage or a rise in claim-class violations counts as a failure, not a win.

---

## 10. Phases and Open Questions

| # | Open question from the PRD | Status | Where | Owner | Due |
|---|---|---|---|---|---|
| 1 | Which agentic CLI | Decided | 4.1, ADR-001 | Deployer | done |
| 2 | Storage format | Decided: Markdown plus YAML in Git, snapshots local | 3, 4.4 | Deployer | done |
| 3 | Data boundary | Decided: C1/C2/C3, three layers, limits stated | 7 | Deployer | done |
| 4 | What to automate first | Decided: phases below | 10 | Deployer + Developer | done |
| 5 | Citation generation and verification | Partly: attribution automated, truth manual | 4.3, 8 | Developer | week 3 |
| 6 | AIBS criteria as a repeatable checklist | Partly: 4 script checks, 8 prompts need the PM's wording | 4.3, 8 | PM | week 3 |
| 7 | Measuring reduction in repetitive work | Decided: self-logged minutes, weekly control source | 9 | Tester | week 2 baseline |
| 8 | Consequence if each assumption is wrong | Research proposal has it, platform side outstanding | proposal 6 | PM | week 3 |
| 9 | Non-coder operability | Test designed, not run | 11 | Tester | week 3 |
| 10 | CLI licence cost and access for five people | Open, blocks the usability test | 4.1 | Deployer | week 2 |

**Phase 1, week 2. Get one source in, correctly.**
`make doctor`, `ingest`, `translate`; `templates/source.md`; `.gitignore` and hook activation; `docs/user-guide.md` first version; baseline timing. Scoring is done **by hand in the YAML** this week, since the arithmetic is trivial and the guide is the real risk. Owner: Deployer. Exit test: a Dutch PDF becomes a complete source file with a snapshot hash, produced by someone other than the Deployer.

**Phase 2, week 3. Score, tag, draft.**
`scripts/score.py` with tiers and claim permissions; `evidence` and `tools` targets; `matrices/usecase-rubric.yaml` with the gate; `redaction_lint.py` and the fieldwork target; `templates/page.md`; `draft` restricted to approved evidence. Owner: Developer, with the Researcher on tagging prompts. Exit test: one page assembled from vault content only, every claim tagged and classed.

**Phase 3, week 4. Enforce.**
`check_claims.py` with the four error classes shown in 4.3; the 4 structural checks and 8 review prompts; `publish`; run-log and time-log summary for the portfolio. Owner: Deployer. Exit test: a deliberately broken draft is blocked with the correct error classes, and a clean draft passes and publishes.

---

## 11. Usability Testing

**Week 3 dry run.** The Tester takes one Dutch public source through ingest and translate using `docs/user-guide.md` only, without help and without seeing the code.

**Pass condition:** the source file is created and committed unaided, and the Tester can state in their own words what that source's tier permits it to support.

**Logged:** commands typed wrongly, error messages that did not say what to do next, steps missing from the guide, any point where the Tester had to guess. Each becomes a fix before phase 3.

**Week 4 second run** covers `draft` and `check` with the PM, so operability is demonstrated for two non-coders rather than one.

---

## 12. Open Technical Questions

| # | Question | Next step | Owner | Due |
|---|---|---|---|---|
| 1 | Sentence-level or paragraph-level claim classification | Run both on one page, compare false positives | Developer | week 3 |
| 2 | Who is the named Dutch reader for statistical and legal terms | Confirm and record in the user guide | PM | week 2 |
| 3 | Do we commit run logs and time logs, given they contain paths | ADR-002, default yes, paths scrubbed | Deployer | week 3 |
| 4 | Which tools get a full dossier, with time for about six | Shortlist from E1 and E3 findings | Researcher | week 3 |
| 5 | Is a 25-word extract cap workable for legal and statutory text | Test on one DPA clause and one CBS table | Researcher | week 3 |
| 6 | Does the safety gate leave any client-facing use case recommendable | Score three real use cases and see | Developer + PM | week 3 |
| 7 | Who assigns claim classes, the agent at draft time or the human at review | Try agent-assigned with human override on one page | Developer | week 3 |

Each returns with a status in the next revision.
