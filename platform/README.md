# AI in Business Handbook

Team repository for the HAN course *AI in Business* (AIBS + AEL). We write an evidence-based handbook for owners of small marketing and advertising agencies on using AI in practice, and we built our own research agent to help produce it.

**Team:** Anastasia, Diana, Maksim, Marija, Md Samsul

## What is where

| What | Where |
|---|---|
| **Research agent** (the AEL platform) | [`platform/`](platform/): see its [README](platform/README.md) to start it |
| **LLM wiki** (our sources, run records and approved pages, checked automatically) | [mkniazevv/ael-llm-wiki](https://github.com/mkniazevv/ael-llm-wiki) |
| **Demo video** | *link to be added* |

### Specification documents (AEL)

| Week | Document |
|---|---|
| 1 | [PRD](week%201%20ael%20prd.md) |
| 2 | [Technical blueprint](Technical_Blueprint.md) and [search strategy](week%202%20search%20strategy.md) (holds the appraisal rubric the agent uses) |
| 3 | [Knowledge architecture](week%203%20ael%20knowledge%20architecture.md) |
| 5 | [First evaluation](week%205%20ael%20first%20evaluation.md) and [decision log](week%205%20decision%20log.md) |

### Handbook pages

| Week | Page |
|---|---|
| 2 | [Geopolitics and vendor models](week%202%20AIBS%20Handbook%20Page%20%E2%80%94%20Geopolitics%20%26%20vendor%20models.md) |
| 3 | [Trust and AI safety](week%203%20trust-and-ai-safety.md) |
| 4 | [SME knowledge gaps](week%204%20sme%20knowledge%20gaps.md) |
| 5 | [AI use cases at SMEs](week%205%20ai%20use%20cases%20at%20smes.md) |

### Other

- Research proposal: [v1](week%201%20research%20proposal.md), [v2](week_1_research_proposal_v2.md)
- [Final interview guide](Final%20interview%20guide.md)
- [Postcard from 2035](week%205%20postcard.md)
- Portfolios: one file per team member (`<name> portfolio.md`)

## Running the research agent

You need Python 3.10 or newer. On Windows, double-click `platform/start.bat`; on Mac or Linux, run `python3 app.py` inside `platform/`. It opens in your browser and runs on your own computer only. Manual mode (copy the prompt to Claude, paste the answer back) needs no API key.

The repository does not contain our research runs, accounts or API settings; they stay on the researchers' computers. The record of every run is in the LLM wiki under `wiki/runs/`.
