# Personal Portfolio - Week 1

## What did I contribute?
During Week 1, I was not able to attend the session, and skipped the initial discussion. However, I caught up with the teammates after the class on their innitial proposal and I helped to draft the AIBS Research Proposal document. Additionally, I reviewed the final draft of week 1 AIBS Research Proposal and AEL Product requierments. 

## What did I do as Deployer?
My designated role in the team is Deployer, whose main task is to get the work "published and reproducible." As well as, making sure a handbook page reaches the shared site, and that someone else on the team could run what I ran. During this first week, I haven't yet had specific deployment tasks, since the project is still in the research and requirements phase. I did start looking into what the role will involve once we move into the building phase, including researching agentic CLIs.

## What do I not understand yet?
After the 1st week I still do not understand how agentic CLI works on the backend such as reading and editing the files, how it connects to the sources and etc. Frontend idea of agentic CLI is clear, as it is a chat-based interface.
I am also unclear on the manual fallback requirement. The PRD states that if automatic extraction, translation or drafting fails, "the researcher must still be able to continue the workflow manually." However, how it would be implemented is still unclear to me. 

# Personal Portfolio - Week 2

## What did team publish?
During Week 2, the team published our first handbook page, Geopolitics and vendor models (in the team repository on 14 September). For AIBS we also compared three AI-written articles claiming that the US, China and Europe each lead in AI, and wrote our search strategy, which holds the source-appraisal rubric (version 1.0) we still use. For AEL, we posted the first version of the Technical Blueprint.

## What did I contribute?
This week, my focus was on advancing both our research and technical documentation:
*Research Proposal:* I collaborated with the team to improve our AIBS research proposal. We incorporated insights from the in-class brainstorming session and answered the Socratic questions to sharpen our main problem statement.
*Technical Blueprint:* I took over the initial draft of the AEL Technical Blueprint and heavily refined it. I focused on solidifying the system architecture, scoring matrices, and the technical workflow to ensure it was fully prepped for the development phase.

## What did I do as Deployer?
In Week 2 there was nothing for me to publish or deploy yet, because the agent did not exist. My work as Deployer was preparing for the build. In the Technical Blueprint I defined how the platform would be built and run, so that in the following weeks the agent could be built from it.

## What feedback did we receive, and what changed?
Our Technical Blueprint and search strategy went to the Socratic tutor, which came back with five questions:

Where does our scoring rubric actually live, and which five criteria does it use? We wrote one explicit rubric in the search strategy (version 1.0) and made the blueprint refer to that same version, so the platform and the researchers score sources the same way.
How can a reviewer appraise a Dutch source before it is translated? We changed the workflow from Ingest → Appraise → Translate to Ingest → Privacy check → Translate if needed → Human appraisal.
Is bias only a problem for commercial AI vendors? No. Government, state-funded, academic and industry sources are now checked for interests and bias too, because authority does not automatically mean independence.

# Personal Portfolio - Week 3

## What did team publish?
During Week 3, the team published the Trust and AI safety handbook page (21 September), with a tester check of the page. For AEL, we wrote the Knowledge Architecture (21 to 25 September), which describes where our sources and drafts live and how the platform finds them. We also prepared our interview guide for the firm visit.

## What did I contribute?
I built Agent v0, the working version of our technical blueprint. I used Claude as a coding assistant to write the code, additionally Samsul helped. My part was deciding what the agent should do, checking every step against our PRD and blueprint, and testing it until it worked for the team. I tested it with real sources. BBC, Guardian and CNN articles were appraised and failed our rubric, which showed the appraisal step can reject weak sources. A Dutch CBS source went through translation, appraisal, evidence selection and review to an approved handbook page. My first version was too complex for the team: it had API connections, a command line and ten test suites. I decided to rebuild it as a simple control panel where each AI step is copy-paste, the manual fallback our PRD allows. After testing it myself, I added features the team needed:

- Going back to change a step without losing earlier work
- English titles for Dutch sources
- PDF input
- Account system, so every decision is recorded under a real name

I also made the demo slides and the script for our presentation.

## What did I do as Deployer?
As Deployer, my task is to get the work "published and reproducible," someone else can run what I ran. This week I made the agent easy to start for the team by implementing a double-click start.bat opens the control panel in the browser, and manual mode needs no API key. The test was whether a teammate could use it without me. On 27 September Samsul ran two sources through the agent himself (RUN-003 and RUN-004, JPMorganChase Institute and CBS) and approved both pages under his own account. 

## What feedback did we receive, and what changed?


# Personal Portfolio - Week 4

## What did team publish?
During Week 4, the team published the SME Knowledge Gaps handbook page (in the team repository on 30 September) and our final interview guide for the Reklaame interview (28 September, revised 4 October). On 28 September we also had the mini-CBI, a short interview with the lecturers about our desk research tool, our new handbook page and our interview guide. For AEL, the fourth document of the week was the build plan.

## What did I contribute?
During Week 4, my main focus was the mini-CBI demo of our research agent. The mini-CBI asked us to show the tool and say where it still falls short, explain why it is agentic (the LLM, skills, tools and context such as the PRD and blueprint), and say what we learned by getting something wrong. On the day of the mini-CBI (28 September) I ran the agent on the Dutch CBS source (RUN-005) as a demonstration. After the mini-CBI I kept working on the agent. On 1 October I saved the old version as a backup and moved to a new design of the control panel to implement features which were suggested during the mini-CBI interview.

## What did I do as Deployer?
This I, as a Deploher, was making sure the agent ran reliably on my laptop for the live demo, with the handbook page and interview guide ready to show next to it. Every run is saved with an activity log, so the demo run can be traced and repeated later.

## What feedback did we receive, and what changed?
The lecturers gave us two pieces of feedback on the agent. First, the appraisal step should learn from the researchers' decisions, using a form of machine learning. Second, the drafted pages sounded too AI-written, so they suggested a rewrite button to make the text sound more natural.

## What do I not understand yet?
After the mini-CBI I did not yet know how to implement machine learning for the appraisal step. Retraining a model was not realistic for our project, so I still had to find a way for the agent to learn from the researchers' corrections without taking the final decision away from them.

# Personal Portfolio - Week 5

## What did team publish?
This week our team focused on AI Use Cases at SMEs. The purpose was to understand which AI applications could provide real business value to small marketing agencies. Additionally, this week an interview with Reklaame was conducted and recorded. A voice recording of an interview was saved and published to the team.

## What did I contribute?
During Week 5, my main focus was setting up our team's LLM Wiki, a repository (ael-llm-wiki) built from the course's wiki template. I added the three sources we had already appraised in our research agent. From them, the wiki now has a page per source, pages for the organisations and seven concept pages. During our interview with Reklaame, I also demonstrated our research agent, showing how it takes a source through translation, appraisal, evidence extraction and a drafted handbook page, with a human decision at every step. I also improved the research agent. I specified three upgrades, and they were built and tested:

- The appraisal step now learns from researchers' corrections. Every time a researcher changes the AI's score, the reason is saved and shown in the next appraisal prompt.
- A switch between manual mode (copy and paste the prompt) and automatic mode (Claude API), with AI settings per account.
- Writing-style rules and a rewrite button, so drafted pages sound less AI-written without changing their citations.

## What did I do as Deployer?
This week I created and published the LLM Wiki on GitHub.

## What feedback did we receive, and what changed?
The most useful feedback was that our interview focused too heavily on productivity. We therefore added questions about what the company does not know about AI, whether it is postponing decisions because of missing information, and how clients' expectations are changing. We also added questions about how employees learn new tools and what AI could mean for junior employees.

## What do I not understand yet?
How to connect the LLM Wiki to an AI chat, so that we can ask it questions and get answers only from the wiki, with citations, instead of opening the pages by hand.


# Personal Portfolio - Week 6

## What did team publish?
During Week 6, the team and I published the work that closes the course and prepares the final assessment. Anastasia posted our "postcard from 2035" to the repository, and the transcript of our Reklaame interview was added. On 13 October I uploaded our research agent to the team repository under platform/. On the AEL side, our LLM wiki now holds every agent run (RUN-001 to RUN-007) and the four approved handbook pages, and it is checked automatically on every change.

## What did I contribute?
During Week 6, my main focus was connecting the LLM Wiki, developed in Week 5, to an AI chat interface. By doing this, it automated the search of already extracted evidence by an agent. With the /wiki command, a question asked in the AI chat is answered only from the LLM Wiki, and every claim, number and evidence is cited accoringly from the Wiki. For example, the question "What are the benefits of AI for small SMEs?" was answered from three sources, and the answer stated openly that the wiki has no evidence that AI saves time or improves quality in agency work, because all three sources focus on adoption.

I also connected the agent to the wiki in the other direction. The new "Send to Wiki" button writes each research run to the LLM Wiki. The AI's suggested scores next to the researcher's decisions, every evidence item with its verbatim quote, and the handbook page once it is approved are sent into LLM Wiki.

## What did I do as Deployer?
As Deployer, my task is to get the work "published and reproducible," the page reaches the shared site, and someone else can run what I ran. This week:

- Published the platform. I uploaded the research agent to the team repository. Before uploading, I made sure private files stay out through .gitignore. It keeps out accounts and API keys.
- Published our runs and pages to the wiki. RUN-001 to RUN-007 and the four approved handbook pages are in the shared wiki (ael-llm-wiki). 
- Automated the check. A GitHub Action runs the wiki check on every push (links, index, and every quote compared word for word with its raw source), and the badge on the wiki README shows whether it passes.

## What feedback did we receive, and what changed?
The most useful feedback was on how to set up and connect LLM Wiki to the AI Chat interface through /wiki command. With this feedback and assitance the LLM Wiki is now succesfully connected to AI chat.

## What do I not understand yet?
Whether evidence and handbooks should stay in the agent or in the wiki. Currently, they are stored in both places, locally in the agent and in the LLM Wiki
