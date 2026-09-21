# Individual Portfolio — Week 1

## What did I contribute?

In Week 1, I contributed to choosing a possible target SME for our handbook project. I helped develop the idea of focusing on small marketing and advertising agencies in Arnhem and Gelderland. Our first possible company is Reklaame in Arnhem.

I contributed to defining the main business problem: marketing agencies may use generative AI to save time on research, brainstorming, first drafts, summaries of client briefs, and creating different versions of marketing content. However, they need to decide carefully which tasks can use AI and which tasks must remain mainly human to protect creative quality, originality, privacy, and client trust.

I also helped prepare the first drafts of the AIBS research proposal and the AEL Product Requirements Document.

## What did I do as Product Manager?

My role in the team is Product Manager. In Week 1, my first task was to help make the project clear and focused. I helped describe who the handbook is for, what problem the handbook should help solve, and what the AI research platform should do.

As Product Manager, I focused on the user journey: a team member adds a source, the platform processes Dutch or English information, translates Dutch material when needed, extracts useful evidence, creates a handbook-page draft, and then the team reviews it before publication.

I also helped make sure that the platform will be easy enough for non-coders to use and that a human team member can check every important step. The AI tool should support the team, but it should not make final decisions or publish pages without human approval.

## What do I not understand yet?

I still do not fully understand how an agentic CLI works in practice. I understand that it is a tool used through commands, but I do not yet know how our team will connect it to sources, translations, AI models, and the GitHub wiki.

I also want to learn more about how the platform will check whether a source is reliable and how it can avoid using incorrect AI-generated information. Another question I have is how we will make the system easy for a non-technical team member to use.

# Week 2 Personal Reflection

## What did our team publish?

This week our team published the handbook page on **geopolitics and vendor models** for small marketing and advertising agencies in the Netherlands. The main idea of the page is that an SME should not only look at which AI tool performs best, but also understand which provider it depends on, where the provider operates, how data is handled, and what could happen if prices, access conditions, regulation or ownership change.

We also completed the Week 2 search strategy and quality criteria and revised the technical blueprint for the research platform.

## What did I contribute?

My main contribution this week was working on the research structure and improving the documents after the Socratic feedback.

I worked on the **Week 2 search strategy**, especially the quality criteria and the changes needed after the teacher questioned how our source appraisal actually worked. I helped make the criteria more specific by introducing a five-part scoring rubric and additional checks for Transparency, Comparability, Traceability and Cross-checking.

I also helped revise the **technical blueprint** so that it matches the research method. One important change was the order for Dutch-language sources. The earlier version used:

**Ingest → Appraise → Translate**

After the feedback, we changed this to:

**Ingest → Eligibility / Privacy Check → Translate if required → Human Appraise**

This makes more sense because a researcher should not fully judge the evidence in a Dutch source if they cannot understand the source before translation.

I also worked on making the research strategy more relevant to our SME by adding searches for European AI alternatives and Dutch, regional and sector-specific sources.

## What did the gates ask, and what did we change?

The Socratic feedback raised five main questions.

First, it asked where our source-scoring rubric actually existed and which five criteria were used. We therefore created one explicit rubric in the Week 2 search strategy and made the technical blueprint refer to the same version.

Second, it questioned how a Dutch source could be appraised before translation. We changed the pipeline so that translation happens before full appraisal when the reviewer cannot understand Dutch.

Third, it questioned our treatment of bias. Our original wording mainly focused on AI vendors, but we changed it so that governments, state-funded organisations, universities and industry organisations are also assessed for relevant interests and possible bias.

Fourth, it pointed out that our search strategy did not really answer E3 about realistic European alternatives. We added product-level searches for specific European providers and practical factors such as pricing, language support, data handling and export possibilities.

Fifth, it pointed out that our search strategy did not include enough Dutch, regional or sector-specific searching for E5 and E6. We therefore added Dutch-language searches involving sources such as KVK, Oost NL, Dutch marketing-sector organisations and provincial sources.

The most important lesson from this feedback was that it is not enough to write good-sounding quality criteria. The criteria must be specific enough that another researcher or the platform can actually apply them consistently.

## What did my build role produce?

My AEL build role was **[WRITE YOUR ROLE HERE: Product Manager / Developer / Tester / Deployer]**.

This week my role contributed to the revision of the technical blueprint and the connection between the AIBS research method and the AEL platform.

The revised blueprint now defines how sources move through the system, how Dutch-language material is handled, where the source-appraisal rubric lives, what information is stored in the source record, and which decisions still require human judgement.

A key improvement is that the platform no longer treats a numerical score as proof that a source is trustworthy. A researcher assigns and explains the scores, while the script only performs the calculation. Human review is still required before evidence is used and before a handbook page is published.

For Week 3, I want to make sure that the next document continues to use the same definitions and does not introduce a different version of the quality criteria or source-handling process.
