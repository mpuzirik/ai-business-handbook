# Personal Portfolio — Week 1

## What did I contribute?
During Week 1, I was not able to attend the session, and skipped the initial discussion. However, I caught up with the teammates after the class on their innitial proposal and I helped to draft the AIBS Research Proposal document. Additionally, I reviewed the final draft of week 1 AIBS Research Proposal and AEL Product requierments. 

## What did I do as Deployer?
My designated role in the team is Deployer, whose main task is to get the work "published and reproducible." As well as, making sure a handbook page reaches the shared site, and that someone else on the team could run what I ran. During this first week, I haven't yet had specific deployment tasks, since the project is still in the research and requirements phase. I did start looking into what the role will involve once we move into the building phase, including researching agentic CLIs.

## What do I not understand yet?
After the 1st week I still do not understand how agentic CLI works on the backend such as reading and editing the files, how it connects to the sources and etc. Frontend idea of agentic CLI is clear, as it is a chat-based interface.
I am also unclear on the manual fallback requirement. The PRD states that if automatic extraction, translation or drafting fails, "the researcher must still be able to continue the workflow manually." However, how it would be implemented is still unclear to me. 

# Personal Portfolio — Week 2

## What did I contribute?
This week, my focus was on advancing both our research and technical documentation:
*Research Proposal:* I collaborated with the team to improve our AIBS research proposal. We incorporated insights from the in-class brainstorming session and answered the Socratic questions to sharpen our main problem statement.
*Technical Blueprint:* I took over the initial draft of the AEL Technical Blueprint and heavily refined it. I focused on solidifying the system architecture, scoring matrices, and the technical workflow to ensure it was fully prepped for the development phase.

# Personal Portfolio — Week 3

## What did I contribute?
I built Agent v0, the working version of our technical blueprint. I used Claude as a coding assistant to write the code, additionally Samsul helped. My part was deciding what the agent should do, checking every step against our PRD and blueprint, and testing it until it worked for the team. I tested it with real sources. BBC, Guardian and CNN articles were appraised and failed our rubric, which showed the appraisal step can reject weak sources. A Dutch CBS source went through translation, appraisal, evidence selection and review to an approved handbook page. My first version was too complex for the team: it had API connections, a command line and ten test suites. I decided to rebuild it as a simple control panel where each AI step is copy-paste, the manual fallback our PRD allows. After testing it myself, I added features the team needed:

- Going back to change a step without losing earlier work
- English titles for Dutch sources
- PDF input
- Account system, so every decision is recorded under a real name

I also made the demo slides and the script for our presentation.


# Personal Portfolio - Week 5

## What did team publish?
This week our team focused on AI Use Cases at SMEs. The purpose was to understand which AI applications could provide real business value to small marketing agencies. Additionally, this week an interview with Reklaame was conducted and recorded. A voice recording of an interview was saved and published to the team.

## What did I contribute?


## What did I do as Deployer?


## What do I not understand yet?
 


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

## What do I not understand yet?
Whether evidence and handbooks should stay in the agent or in the wiki. Currently, they are stored in both places, locally in the agent and in the LLM Wiki
