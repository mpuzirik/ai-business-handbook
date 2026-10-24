# AI in Business Handbook

Team repository for the HAN course *AI in Business* (AIBS + AEL). We write an evidence-based handbook for owners of small marketing and advertising agencies on using AI in practice, and we built our own research agent to help produce it.

**Team:** Anastasia, Diana, Maksim, Marija, Md Samsul

## What is where

| What | Where |
|---|---|
| **Research agent** (the AEL platform) | [`platform/`](platform/): see *Running the research agent* below |
| **LLM wiki** (our sources, run records and approved pages, checked automatically) | [mkniazevv/ael-llm-wiki](https://github.com/mkniazevv/ael-llm-wiki) |
| **Demo video** | [Watch the 5-minute demo](https://hannl-my.sharepoint.com/personal/m_kniazev_student_han_nl/_layouts/15/stream.aspx?id=%2Fpersonal%2Fm%5Fkniazev%5Fstudent%5Fhan%5Fnl%2FDocuments%2F%D0%97%D0%B0%D0%BF%D0%B8%D1%81%D1%8C%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026%2D10%2D23%20205954%2Emp4&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0&ga=1&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E42058951%2D386e%2D485d%2Db3b0%2D1148335c686f) |

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
| 5 | [Theme 4: Where should a small marketing agency use AI first?](Handbook_Reklaame_Theme4_v1.1.docx) (replaces the earlier [AI use cases page](week%205%20ai%20use%20cases%20at%20smes.md), written before the interview) |

### Other

- Research proposal: [v1](week%201%20research%20proposal.md), [v2](week_1_research_proposal_v2.md)
- [Final interview guide](Final%20interview%20guide.md)
- [Postcard from 2035](week%205%20postcard.md)
- Portfolios: one file per team member (`<name> portfolio.md`)

## Running the research agent

You need Python 3.10 or newer. On Windows, double-click `platform/start.bat`; on Mac or Linux, run `python3 app.py` inside `platform/`. It opens in your browser and runs on your own computer only. Manual mode (copy the prompt to Claude, paste the answer back) needs no API key.

The repository does not contain our research runs, accounts or API settings; they stay on the researchers' computers. The record of every run is in the LLM wiki under `wiki/runs/`.
