# AIBS Assignment 2 — Search Strategies and Quality Criteria

## 1. Source Quality Criteria

Before searching for reports, we defined the criteria that we would use to decide whether a source was suitable for our research. Since the topic is the geopolitical AI race between the United States, China and Europe, a source should provide evidence that can be traced and compared rather than simply giving an opinion about which region is leading.

A good-quality source should meet the following criteria:

- **Authority:** The author or organisation must be clearly identifiable and have relevant expertise.

- **Evidence:** Important claims should be supported by data, references or a clearly explained research method.

- **Recency:** We prioritise recent sources because AI capabilities, investment, regulation and adoption are changing quickly.

- **Transparency:** The source should explain where its information comes from and, where relevant, how indicators were measured.

- **Relevance:** The source must provide information that directly or indirectly helps answer one of our research questions.

- **Comparability:** Statistics should clearly identify the country or region, measurement period, definition and indicator being measured so that different figures are not compared out of context.

- **Independence and bias:** We examine relevant interests for every publisher, including companies, governments, state-funded institutes, universities and industry organisations. An official or government source is not automatically independent simply because it is authoritative. Claims about a country's own AI leadership require examination of the method and, where possible, independent corroboration.

- **Traceability:** Important claims used in our final handbook should be traceable back to the original source, including the relevant section, table or passage where possible.

- **Cross-checking:** Important, disputed or self-interested claims should, where possible, be checked against another independent source. Two publications repeating the same original dataset do not count as two independent confirmations.

We do not define AI leadership using a single measurement. Instead, we consider several dimensions, including frontier AI models, research, investment, computing capacity, patents, business adoption and regulation.

These criteria were defined so that sources are selected according to their quality and relevance rather than according to whether they support a conclusion we already expect.

### 1.1 Source-Appraisal Rubric

Following the Socratic feedback, we made the source-appraisal method explicit.

The authoritative version of the rubric is maintained in this section of `week 2 search strategy.md`. The AEL technical blueprint and source-record structure must refer to this same rubric so that the research method and the platform use the same quality criteria.

**Rubric version: 1.0**

Five of the nine quality criteria receive a numerical score.

Each scored criterion has equal weight and receives **0, 1 or 2 points**.

| Criterion | 0 points | 1 point | 2 points |
|---|---|---|---|
| **Authority** | The author or relevant expertise cannot be established. | The author is identifiable but relevant expertise is only partly established. | Relevant expertise or responsibility is clearly established. |
| **Evidence** | The intended claim has no verifiable supporting evidence. | Some supporting evidence exists but important limitations remain. | Evidence clearly supports the intended claim and the method is explained where relevant. |
| **Recency** | The information is outdated for the intended use. | Older information remains useful, but its limitations must be stated. | The information is sufficiently current for the research question. |
| **Relevance** | The source does not help answer a research question. | The source provides useful background. | The source directly addresses a named research question. |
| **Independence and bias** | Relevant interests or one-sided presentation are not addressed. | Relevant interests are identified but some concerns remain. | Relevant interests and limitations are documented and independent checking is completed where necessary. |

**Maximum score: 10 points.**

### Provisional source tiers

- **8–10 points — Tier A:** eligible for use as core evidence, subject to the additional checks below.
- **5–7 points — Tier B:** suitable mainly for background or limited claims, with limitations stated.
- **0–4 points — Tier C:** not accepted as supporting evidence for the handbook.

The four remaining criteria are treated as additional checks rather than extra numerical scores:

- **Transparency:** Are the source's data, definitions and methods sufficiently visible?
- **Comparability:** Are the geography, period, units and definitions genuinely comparable with the evidence being compared?
- **Traceability:** Can the supporting passage, table or section be located?
- **Cross-checking:** Has an important, disputed or self-interested claim been independently checked?

A high numerical score does not override these checks.

For example, a prestigious source cannot be used to support a claim that is not actually present in the source. A failed comparability check means that two statistics should not be directly compared even when both sources have high scores.

A researcher assigns the scores and records the reason for each score. A script may calculate the total and provisional tier, but the script does not decide whether a claim is true or whether it should be published.

The source record should therefore store:

- rubric version;
- five individual scores;
- total score;
- provisional tier;
- transparency result;
- comparability result;
- traceability information;
- cross-checking status;
- reviewer;
- review date;
- intended use of the source;
- final human decision.

### 1.2 Appraising Dutch-Language Sources

The Socratic feedback identified a problem in our original pipeline: it placed appraisal before translation even though not every team member can necessarily evaluate a Dutch source in Dutch.

We therefore distinguish between an **initial source check** and a **full evidence appraisal**.

The revised process is:

**Ingest → initial eligibility and privacy check → translate if required → human appraisal**

During the initial check, the researcher can record information that does not require detailed interpretation of the content, such as:

- publisher;
- author;
- publication date;
- source type;
- original language;
- accessibility;
- whether the source is permitted within the project's privacy boundary.

A researcher who understands Dutch may appraise the original Dutch source directly.

If the reviewer cannot adequately understand the Dutch source, an English working translation must be produced before completing the full evidence appraisal.

The translation must include the relevant evidence, definitions, methods and limitations. A short summary containing only the main conclusion is not sufficient for assessing Evidence or Comparability.

The original Dutch source must remain available and important translated claims must remain linked to the original passage.

Translation does not create a new source and does not make the original source more reliable.

If an important Dutch claim cannot be checked adequately, the claim remains pending and should not be treated as verified evidence.

The existing privacy boundary still applies. Translation does not allow confidential or restricted material to be sent to a model or service that is not permitted to receive it.

---

## 2. Search Strategy

After defining the source-quality criteria, we searched for recent and credible reports that could help compare the geopolitical position of the United States, China and Europe in artificial intelligence.

Instead of searching only for a general answer to the question “Who leads AI?”, we divided the topic into several measurable areas:

1. frontier AI models and model performance;
2. AI research and scientific publications;
3. patents and innovation;
4. access to advanced computing infrastructure;
5. private AI investment;
6. business and industrial adoption;
7. regulation and government policy;
8. strategic dependence on foreign AI technologies.

We prioritised primary and institutional sources because these are generally more useful for evidence-based comparison than unsupported opinion articles or AI-generated summaries.

However, following the Socratic feedback, we no longer treat government or institutional status as automatic evidence of independence. The intended claim, method, institutional interest and possible bias must still be assessed.

The main organisations used in the first search round included:

- Stanford Institute for Human-Centered Artificial Intelligence;
- OECD;
- World Intellectual Property Organization (WIPO);
- European Commission;
- official public-sector and research organisations.

Example queries from the first search round included:

- `US China Europe AI competition report`
- `Stanford AI Index US China Europe`
- `China US Europe AI patents WIPO`
- `AI investment US China EU OECD`
- `Draghi report AI Europe competitiveness`
- `AI compute capacity US China Europe`
- `AI research publications China US Europe`
- `EU AI Act general purpose AI providers`

We searched by individual dimension rather than expecting one report to answer the complete geopolitical question.

This approach was chosen because AI leadership is multidimensional. A country or region may lead in model development but not in patents, investment, regulation or industrial deployment.

Where an important claim was identified, we attempted to compare it with evidence from another institution or dataset before using it in the handbook.

### 2.1 Product-Level Search for European Alternatives — E3

The Socratic feedback showed that our original search strategy was too focused on national-level indicators to answer E3:

**Are there European alternatives that a Dutch agency can realistically use?**

Model counts, patents and investment statistics cannot answer this question by themselves.

We therefore added a separate product-level search strategy.

Example queries include:

- `Mistral AI business assistant pricing Netherlands`
- `Mistral AI Dutch language marketing content`
- `Mistral AI business data processing EU`
- `Mistral AI marketing case study`
- `European generative AI assistant small business Netherlands`
- `European AI tool marketing agency business alternative ChatGPT`

A named provider in a query is a research candidate, not an automatic recommendation.

For each possible European alternative, the research should investigate:

- provider and country;
- relevant product and subscription plan;
- availability to a Dutch SME;
- price;
- language support;
- relevant marketing capabilities;
- data-processing arrangements;
- retention and export possibilities;
- business or administrative controls;
- evidence of practical performance.

Provider documentation can be used as a primary source for the provider's own pricing, features and contractual terms.

However, a provider's own statements about the quality or superiority of its product are not treated as independent evidence of performance.

Practical suitability therefore requires either independent evidence or a documented test.

### 2.2 Dutch-Language, Regional and Sector-Specific Searches — E5 and E6

Our first search round was mostly in English and concentrated on international institutions.

This did not adequately reflect the Dutch, regional and marketing-sector evidence needs identified in E5 and E6.

We therefore added Dutch-language searches in three areas:

1. **AI adoption and responsible use by Dutch SMEs;**
2. **AI adoption within the Dutch marketing sector;**
3. **regional support, funding and implementation opportunities relevant to a company in Arnhem/Gelderland.**

Example searches include:

- `KVK generatieve AI mkb`
- `KVK AI beleid bedrijf`
- `KVK generatieve AI marketing`
- `DDMA generatieve AI marketing onderzoek Nederland`
- `marketingsector AI gebruik Nederland onderzoek`
- `Oost NL AI mkb Gelderland`
- `Oost NL digitalisering AI ondernemers`
- `provincie Gelderland digitalisering mkb subsidie`
- `Gelderland AI mkb ondersteuning`
- `Gelderland innovatie digitalisering subsidie mkb`

These searches have a different purpose from the international searches.

International sources are used mainly to understand the wider geopolitical AI ecosystem.

Dutch and regional sources are used to investigate practical adoption, local support, sector experience and implementation conditions that may matter to a Dutch marketing agency.

A regional source is not used as evidence about the entire Dutch marketing sector or about global AI leadership unless its scope supports that conclusion.

Similarly, one marketing-company example cannot be generalised to all agencies.

### 2.3 What Changes When We Search in Dutch?

Running part of the research in Dutch changes both the evidence base and the appraisal process.

For example:

- international investment reports may tell us where AI capital is concentrated;
- Dutch marketing-sector research may tell us how AI is actually being used by marketing organisations in the Netherlands;
- KVK guidance may help identify practical governance concerns for Dutch SMEs;
- regional organisations such as Oost NL may identify local programmes or implementation support;
- provincial sources may identify current funding opportunities or eligibility conditions.

The search therefore becomes more useful to the SME because it combines global geopolitical evidence with local implementation evidence.

It also makes the Translate stage of our platform meaningful: the team can include relevant Dutch evidence even when not every researcher speaks Dutch fluently.

### 2.4 Search Record

To make the search repeatable, future searches will be recorded using the following structure:

| Search date | Research question | Search location | Exact query | Source selected | Include/exclude reason |
|---|---|---|---|---|---|

This makes it possible for another team to see not only which sources we selected, but also how we reached them.

---

## 3. Selected Sources and Initial Appraisal

The numerical scores below apply to the **specific intended use of each source**, not to the organisation as a whole.

### Stanford AI Index 2026

**Source:** Stanford Institute for Human-Centered Artificial Intelligence — *The 2026 AI Index Report*

**Why we selected it:**  
The Stanford AI Index provides a broad international comparison of AI research, model development, technical performance, computing infrastructure, investment and adoption. It separates different dimensions rather than treating AI leadership as one measurement.

**Relevant evidence:**  
The report shows that China leads in AI publication volume, citations and patent grants, while the United States continues to lead in notable AI model development. U.S.-based institutions produced **59 notable AI models in 2025 compared with 35 from China**.

The report also finds that the performance gap between leading U.S. and Chinese models has become very small.

The report identifies a major computing-infrastructure advantage for the United States and also highlights international dependence in advanced semiconductor production.

**Limitations:**  
Indicators such as notable models, publications, citations and infrastructure measure different dimensions. None alone demonstrates overall AI dominance.

**Initial rubric score:**

- Authority: 2
- Evidence: 2
- Recency: 2
- Relevance: 2
- Independence and bias: 1
- **Total: 9/10 — Tier A**

**Additional checks:**  
The institution is U.S.-based, so comparative claims about U.S. leadership should still be checked against other international evidence. Relevant measurements are cross-checked where possible using OECD and WIPO.

### OECD — AI Venture Capital Investment

**Source:** OECD — *Venture capital investments in artificial intelligence through 2025*

**Why we selected it:**  
The OECD publishes comparable cross-country economic data and describes the methodology behind the analysis.

**Relevant evidence:**  
In 2025, U.S. AI firms received approximately **75% of global AI venture-capital deal value, around USD 194 billion**. EU27 firms received around **6%, or USD 15.8 billion**, while China received around **5%, or USD 13.9 billion**.

**Limitations:**  
Venture-capital investment measures private capital but does not directly measure model performance, public investment, research strength or adoption.

**Initial rubric score:**

- Authority: 2
- Evidence: 2
- Recency: 2
- Relevance: 2
- Independence and bias: 2
- **Total: 10/10 — Tier A**

**Additional checks:**  
The figures are suitable for investment comparison only and are not used as a general ranking of technological capability.

### WIPO — Patent Trends Update in GenAI 2026

**Source:** World Intellectual Property Organization — *Patent Trends Update in GenAI*, 2026

**Why we selected it:**  
WIPO is a United Nations specialised agency responsible for international intellectual-property systems. Its analysis provides comparable patent-family evidence.

**Relevant evidence:**  
Global generative-AI patent activity increased rapidly through 2025.

China remains the largest source of GenAI patent activity, while the United States is also increasing its activity.

**Limitations:**  
Patent volume measures inventive activity rather than commercial success or model performance. Filing practices differ between countries.

**Initial rubric score:**

- Authority: 2
- Evidence: 2
- Recency: 2
- Relevance: 2
- Independence and bias: 2
- **Total: 10/10 — Tier A**

**Additional checks:**  
Patent counts are never interpreted on their own as proof that one country has better AI technology.

### European Commission — Draghi Report on EU Competitiveness

**Source:** European Commission — *The Future of European Competitiveness*, commonly known as the Draghi Report

**Why we selected it:**  
The report was commissioned to analyse structural challenges affecting European competitiveness, investment and innovation.

**Relevant evidence:**  
The report argues that Europe requires stronger investment and innovation capacity to remain competitive in digital technologies and other strategic industries.

**Limitations:**  
This is a European policy and competitiveness report, not a neutral global AI ranking.

Because it was commissioned by the European Commission and is concerned specifically with European competitiveness, its institutional context is relevant to the bias assessment.

**Initial rubric score:**

- Authority: 2
- Evidence: 2
- Recency: 1
- Relevance: 2
- Independence and bias: 1
- **Total: 8/10 — Tier A**

**Additional checks:**  
Claims about Europe's relative position are compared with external quantitative sources such as Stanford and OECD rather than accepted solely because they appear in the Draghi Report.

### European Commission — EU AI Act

**Source:** European Commission — official information and guidance about the EU Artificial Intelligence Act

**Why we selected it:**  
For questions about what EU regulation requires, the European Commission is an appropriate primary institutional source.

**Relevant evidence:**  
The source explains obligations affecting general-purpose AI providers and the implementation of the AI Act in the European market.

**Limitations:**  
An official EU source is appropriate for identifying EU rules, but it is not independent evidence that European regulation is superior or that Europe leads technologically.

**Initial rubric score:**

- Authority: 2
- Evidence: 2
- Recency: 2
- Relevance: 2
- Independence and bias: 1
- **Total: 9/10 — Tier A**

**Additional checks:**  
The source is used for regulatory facts, not as evidence of European technological superiority.

---

## 4. Why These Sources Are Stronger Than the Assignment 1 Articles

The AI-generated articles from Assignment 1 gave confident answers about which region leads in AI, but the evidence behind many claims was unclear or inconsistent.

The sources selected here improve on that approach because important claims can be linked to identifiable organisations, datasets and measurement methods.

They also show why the question **“Who dominates AI?”** is too simple.

Different indicators produce different pictures:

- the United States has strong evidence in private AI investment, notable model development and computing infrastructure;
- China has strong evidence in research activity and generative-AI patenting and is increasingly competitive in frontier models;
- Europe has a smaller private AI investment scale but significant regulatory influence and a large market in which global AI providers operate.

These statements describe different dimensions and are not combined into a single overall ranking.

The new appraisal rubric also means that authority alone is no longer enough. A government, company, university or international organisation can still have interests or methodological limitations that must be recorded.

---

## 5. First AI-Assisted Analysis

After selecting and appraising the initial international sources, we used AI to compare the United States, China and Europe using only the evidence supplied from those sources rather than asking the model to independently decide who dominates AI.

The instruction used for the analysis was:

> Compare the United States, China and Europe using only the evidence provided in the selected sources. Analyse frontier AI capability, research output, patents, investment, compute and regulation separately. Identify which source supports each important conclusion. Where sources disagree or measure different things, explain the difference instead of choosing one claim without justification. Do not describe one region as the overall AI leader unless the evidence supports that conclusion across several dimensions.

### United States

The strongest evidence for the U.S. position is currently in frontier-model development, private investment and computing infrastructure.

According to the Stanford AI Index 2026, U.S.-based institutions produced **59 notable AI models in 2025 compared with 35 from China**.

However, Stanford also reports that the performance gap between leading U.S. and Chinese models has become very small. Therefore, the number of notable models should not automatically be interpreted as proof that U.S. models are always technically superior.

OECD data shows a much larger difference in private investment. In 2025, U.S.-based AI firms attracted approximately **75% of global AI venture-capital deal value**.

The United States also has a substantial data-centre presence.

At the same time, advanced AI supply chains remain internationally dependent, including dependence on semiconductor manufacturing outside the United States.

The evidence therefore supports a strong U.S. position in several dimensions but does not establish U.S. leadership in every area of AI.

### China

China's strongest position appears in research activity, patenting and increasingly competitive AI models.

The Stanford AI Index reports strong Chinese research activity and a much smaller performance gap between leading U.S. and Chinese models than in previous years.

WIPO's patent evidence also shows very high levels of Chinese generative-AI patent activity.

However, patent volume should not automatically be interpreted as technological or commercial dominance.

Patent counts do not show whether an invention becomes commercially successful, how economically significant it is, or whether it directly improves frontier-model performance.

### Europe

Europe has a different position from the United States and China.

OECD evidence shows a large difference in private AI venture-capital investment between the EU and the United States.

The Draghi Report identifies Europe's difficulty in converting research and innovation into globally scaled technology businesses as a competitiveness challenge.

Europe also has significant regulatory influence through the EU AI Act.

However, regulatory influence is different from technological or commercial leadership.

The EU's official sources are therefore used to identify European rules and policy, not as independent proof that Europe leads the global AI industry.

### European Alternatives and Dutch Context

The Socratic feedback showed that our first analysis did not adequately answer whether a Dutch marketing agency has practical European alternatives or what Dutch and regional evidence means for implementation.

We therefore added separate E3, E5 and E6 search routes in Section 2.

These searches focus on:

- specific European products and providers;
- practical availability and business conditions;
- Dutch SME guidance;
- Dutch marketing-sector evidence;
- regional implementation support;
- and relevant funding opportunities.

Findings from these searches should be added to this analysis only after the sources have been appraised using the same rubric.

---

## 6. Comparison

The evidence does not support the idea that one country or region dominates every part of artificial intelligence.

Instead, the evidence points to different strengths across different indicators.

- **United States:** particularly strong in notable model development, private AI investment and computing infrastructure.
- **China:** particularly strong in research activity and generative-AI patenting, with increasingly competitive frontier models.
- **Europe/EU:** smaller private AI investment scale but significant regulatory influence and a major market for AI services.

This differs from the AI-generated articles in Assignment 1.

Those articles began with a requested conclusion and then generated an argument supporting it.

In this analysis, the intended process is the reverse:

**define the criteria → search → appraise the sources → compare the evidence → then draw a conclusion.**

The main finding is therefore that **“AI leadership” depends on what is being measured**.

Model development, performance, investment, publications, patents, computing infrastructure, adoption and regulation are different indicators and should not be combined into a single ranking without explanation.

---

## 7. Relevance to Our SME

For our target audience — **small marketing and advertising agencies in the Netherlands** — the geopolitical question becomes more practical.

Our preferred case company, **Reklaame**, is based in Arnhem.

An agency owner is unlikely to need a simple answer about whether the United States, China or Europe “wins” the AI race.

The more useful questions are:

- Which AI services does the agency depend on?
- Where are the providers based?
- What data and contractual conditions apply?
- Are realistic European alternatives available?
- Could important work be moved to another provider?
- Which Dutch rules and guidance apply?
- Is relevant regional support available?

A small marketing agency may depend on foreign providers for:

- generative text;
- image generation;
- AI-assisted design;
- cloud services;
- productivity tools;
- and other digital infrastructure.

Changes in pricing, access conditions, data-processing policies or regulation may therefore affect the agency even if it does not operate internationally.

The international research helps identify geopolitical dependencies.

The E3 product-level research will help investigate practical alternatives.

The E5 and E6 Dutch and regional searches will help determine what is relevant to the selected SME's local business environment.

Regional evidence will not be generalised to all Dutch marketing agencies unless its scope supports that conclusion.

---

## 8. Initial Conclusion

The first evidence-based analysis suggests that the United States has a strong position in several commercially important dimensions of the AI ecosystem, particularly notable model development, private investment and computing infrastructure.

China has a strong position in research and generative-AI patent activity, while its leading models have become increasingly competitive.

Europe has less private AI investment at the scale measured by the OECD but remains important through research, regulation and its position as a major market.

However, the Socratic feedback demonstrated that this international comparison alone is not sufficient for our full research proposal.

To answer the questions that matter to a Dutch marketing agency, the next search layer must also investigate:

- usable European alternatives;
- Dutch SME practice;
- the Dutch marketing sector;
- and relevant regional support.

The purpose of the research is therefore not to declare one country the overall winner.

For the handbook audience, the more useful outcome is to understand **which dependencies exist, which alternatives are realistic, and what the SME can do if those dependencies change.**

---

## 9. Response to Socratic Feedback

### Question 1 — Where does the scoring rubric live and which five criteria does it use?

The rubric now lives in **Section 1.1 of `week 2 search strategy.md`** and is labelled version 1.0.

The five scored criteria are:

1. Authority;
2. Evidence;
3. Recency;
4. Relevance;
5. Independence and bias.

Transparency, Comparability, Traceability and Cross-checking remain mandatory additional checks.

The technical blueprint and source-record contract must refer to this same rubric rather than define a different one.

### Question 2 — How can a Dutch source be appraised before translation?

The workflow has been clarified.

The first step is now only an initial eligibility and privacy check.

Full evidence appraisal occurs after translation when the reviewer cannot adequately understand Dutch.

A Dutch-speaking reviewer may appraise the original directly.

The original source remains linked to the translation, and uncertain claims remain pending rather than being treated as verified.

The technical blueprint must therefore change from:

**Ingest → Appraise → Translate**

to:

**Ingest → eligibility/privacy check → Translate if required → Human Appraise**

### Question 3 — How are government and state-funded sources treated?

Government status no longer automatically results in a source being treated as independent.

Government, state-funded, corporate, academic and industry sources are all assessed for relevant interests and institutional context.

An official source may be the strongest primary source for what a government programme or regulation says.

However, a government source claiming that its own country leads AI requires methodological examination and independent corroboration before being treated as evidence of leadership.

### Question 4 — How will E3 be searched directly?

A new product-level search strategy has been added in Section 2.1.

Instead of only searching national indicators such as investment or patents, E3 searches named providers and products and investigates practical factors such as pricing, language support, availability, data processing and exportability.

European providers identified in the search are candidates for appraisal and testing, not automatically recommendations.

### Question 5 — Where are the Dutch, regional and sector-specific searches?

A new Dutch-language search strategy has been added in Sections 2.2 and 2.3.

The new search routes include:

- KVK for Dutch SME guidance;
- Dutch marketing-sector research;
- Oost NL for regional AI and digitalisation support;
- Province of Gelderland sources for relevant programmes and funding.

These sources answer a different question from international AI-leadership reports and will therefore be used specifically for Dutch SME, sector and regional context.

The new searches also provide a practical reason for the platform's Dutch-language translation workflow.

---

## AI Use and Human Review

AI was used to support drafting, restructuring and the first analysis.

The team remains responsible for:

- checking the original sources;
- confirming rubric scores;
- conducting and documenting the new E3, E5 and E6 searches;
- verifying translated evidence;
- deciding which claims are suitable for the handbook;
- and recording changes resulting from the Socratic feedback.
