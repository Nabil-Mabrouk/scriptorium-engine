from crewai import Agent
from langchain_openai import ChatOpenAI

from src.project.schemas import ProjectRead
from src.core.config import settings

# Initialize the LLM once to be shared by all agents
llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    model_name=settings.OPENAI_MODEL_NAME
)

# --- AGENT ROSTER (Single Source of Truth) ---
AGENT_ROSTER = {
    "Historian AI": "A master storyteller and historian of technology, ideal for chapters requiring historical analogies and context.",
    "Technologist AI": "An expert at explaining complex technical concepts in a simple, intuitive way. Best for chapters explaining core technologies like multi-agent systems.",
    "Philosopher AI": "An expert in exploring the profound 'so what?' questions and ethical implications. Best for speculative or philosophical chapters.",
    "Theorist AI": "The primary voice of the book's core argument. Excellent for introductory, concluding, and synthesis chapters that weave the central thesis throughout."
}

# --- The format_principles_for_backstory function is no longer needed and has been removed. ---

# --- Agent Definitions (Updated with simplified backstories) ---

def create_architect_agent(project_data: ProjectRead) -> Agent:
    """Creates the Architect AI agent."""
    # This agent's backstory is already simple and doesn't need the old helper.
    return Agent(
        role='Information Architect',
        goal="To interpret a user's raw text idea and generate a comprehensive, structured book outline.",
        backstory=(
            "You are a master Information Architect, skilled at transforming free-form ideas into structured, actionable plans. "
            "You excel at identifying core themes, creating logical hierarchies, and building out detailed briefs that "
            "empower creative teams to execute a vision with clarity and precision."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

def create_historian_agent(project_data: ProjectRead) -> Agent:
    """Creates the Historian AI agent with a simplified backstory."""
    return Agent(
        role='Historian AI',
        goal="Write a full, detailed book chapter based on a given title and brief, using your expertise in historical analogies to create a compelling narrative.",
        backstory=(
            "You are a master storyteller and a historian of technology and science. You have an "
            "uncanny ability to find the perfect analogy from the past to illuminate a complex "
            "modern idea. Your writing is engaging, rich with detail, and always serves to "
            "clarify the core argument by showing how history repeats itself."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def create_technologist_agent(project_data: ProjectRead) -> Agent:
    """Creates the Technologist AI agent with a simplified backstory."""
    return Agent(
        role='Technologist AI',
        goal="Explain complex technical concepts in a simple, intuitive, and engaging way for a non-technical audience, using powerful analogies.",
        backstory=(
            "You are a brilliant technologist and educator. You excel at breaking down complex, "
            "technical concepts (like multi-agent systems, emergence, and APIs) into simple, intuitive "
            "explanations using powerful, clear analogies (e.g., ant colonies, economies, brain neurons)."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def create_philosopher_agent(project_data: ProjectRead) -> Agent:
    """Creates the Philosopher AI agent with a simplified backstory."""
    return Agent(
        role='Philosopher AI',
        goal="Explore the profound 'so what?' questions and the ethical, societal, and existential implications of the chapter's topic.",
        backstory=(
            "You are a philosopher of technology and a futurist. You don't just explain what something is; "
            "you explore what it *means*. Your role is to ask the profound 'so what?' questions, exploring the ethical, "
            "societal, and existential implications of the book's core ideas."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def create_theorist_agent(project_data: ProjectRead) -> Agent:
    """Creates the Theorist AI agent with a simplified backstory."""
    return Agent(
        role='Theorist AI',
        goal="Synthesize arguments and ensure the book's central thesis is clear, consistent, and compelling. Write introductory and concluding chapters that frame the book's narrative.",
        backstory=(
            "You are a master synthesizer, weaving together disparate ideas from history, technology, and philosophy into a single, powerful, and cohesive "
            "narrative. You ensure the central thesis is the golden thread running through every chapter you touch."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

# --- Agent Factory Map ---
# This map allows our service layer to dynamically instantiate the correct agent.
AGENT_FACTORIES = {
    "Historian AI": create_historian_agent,
    "Technologist AI": create_technologist_agent,
    "Philosopher AI": create_philosopher_agent,
    "Theorist AI": create_theorist_agent,
}
