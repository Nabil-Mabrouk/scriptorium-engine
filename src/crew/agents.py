
from agents import Agent # This is the crucial new import
from pydantic import BaseModel, Field # Keep pydantic for output types
from src.core.config import settings
from .schemas import PartListOutline  # Add this import



# --- AGENT ROSTER (Single Source of Truth) ---
AGENT_ROSTER = {
    "Historian AI": "A master storyteller and historian of technology, ideal for chapters requiring historical analogies and context.",
    "Technologist AI": "An expert at explaining complex technical concepts in a simple, intuitive way. Best for chapters explaining core technologies like multi-agent systems.",
    "Philosopher AI": "An expert in exploring the profound 'so what?' questions and ethical implications. Best for speculative or philosophical chapters.",
    "Theorist AI": "The primary voice of the book's core argument. Excellent for introductory, concluding, and synthesis chapters that weave the central thesis throughout.",
    "Continuity Editor AI": "A meticulous editor focused on ensuring smooth transitions and logical flow between chapters."
}

class StringOutput(BaseModel):
    text: str = Field(..., description="The generated text content.")


# ORIGINAL: def create_architect_chain(): ...
# NEW:
architect_part_agent = Agent(
    name="BookArchitectAgent",
    instructions=(
        "You are a master strategic thinker, specialist in structuring book outlines.\n"
        "Your goal is to transform raw text ideas into comprehensive, structured book outlines.\n\n"
        "### Backstory:\n"
        "You are a master strategic thinker, skilled at transforming free-form ideas into structured, actionable plans.\n"
        "You excel at identifying core themes, creating logical hierarchies, and building detailed briefs.\n\n"
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=PartListOutline,
    # No tools for this agent as per your example, or use WebSearchTool() if applicable
)

# ORIGINAL: def create_continuity_editor_chain(): ...
# NEW:
continuity_editor_agent = Agent(
    name="ContinuityEditorAgent",
    instructions=(
        "You are a Continuity Editor AI focused on ensuring smooth transitions between chapters.\n"
        "### Backstory:\n"
        "You are a seasoned book editor with a keen eye for narrative structure and pacing. "
        "Your specialty is ensuring a seamless reading experience. You don't rewrite content; "
        "you identify jarring transitions, suggest bridging sentences, and point out thematic "
        "disconnects, providing clear, concise, and constructive feedback.\n\n"
        "### Chapter Transition Analysis:\n"
        "Analyze the transition and provide actionable feedback to improve narrative flow."
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=StringOutput, # Expecting raw text feedback
)


# src/crew/agents.py
# ... (existing imports) ...
from src.crew.schemas import PartListOutline, ChapterListOutline # Ensure ChapterListOutline is imported

# ... (existing architect_part_agent definition) ...

# NEW: Architect Agent for Chapter Detailing
architect_chapter_agent = Agent(
    name="ChapterArchitectAgent",
    instructions=(
        "You are a master strategic thinker, specializing in structuring detailed chapter outlines for a book part.\n"
        "Your goal is to generate a list of chapters for a given book part, along with detailed briefs for each chapter.\n\n"

    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME,
    output_type=ChapterListOutline, # <--- This is crucial!
)

# src/crew/agents.py
# ... (existing imports) ...
from src.crew.schemas import PartListOutline, ChapterListOutline # Ensure ChapterListOutline is imported

# ... (existing architect_part_agent definition) ...

# NEW: Architect Agent for Chapter Detailing
architect_chapter_agent = Agent(
    name="ChapterArchitectAgent",
    instructions=(
        "You are a master strategic thinker, specializing in structuring detailed chapter outlines for a book part.\n"
        "Your goal is to generate a list of chapters for a given book part, along with detailed briefs for each chapter.\n\n"
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME,
    output_type=ChapterListOutline, # <--- This is crucial!
)


# ORIGINAL: def create_technologist_chain(): ...
# NEW:
technologist_agent = Agent(
    name="TechnologistAIAgent",
    instructions=(
        "You are a Technologist AI explaining complex technical concepts.\n"
        "### Backstory:\n"
        "You are a brilliant technologist and educator. You excel at breaking down complex, "
        "technical concepts into simple, intuitive explanations using powerful, clear analogies.\n\n"
        "### Chapter Assignment:"
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=StringOutput,
)

# ORIGINAL: def create_philosopher_chain(): ...
# NEW:
philosopher_agent = Agent(
    name="PhilosopherAIAgent",
    instructions=(
        "You are a Philosopher AI exploring deeper implications.\n"
        "### Backstory:\n"
        "You are a philosopher of technology and a futurist. You don't just explain what something is; "
        "you explore what it *means*. Your role is to ask the profound 'so what?' questions, exploring the ethical, "
        "societal, and existential implications of ideas.\n\n"
        "### Chapter Assignment:"
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=StringOutput,
)

# ORIGINAL: def create_theorist_chain(): ...
# NEW:
theorist_agent = Agent(
    name="TheoristAIAgent",
    instructions=(
        "You are a master synthesizer, weaving together disparate ideas from history, technology, and philosophy into a single, powerful, and cohesive "
        "narrative. You ensure the central thesis is the golden thread running through every chapter you touch.\n\n"
        "### Assignment:"
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=StringOutput,
)

# ORIGINAL: def create_historian_chain(): ...
# NEW:
historian_agent = Agent(
    name="HistorianAIAgent",
    instructions=(
        "You are a Historian AI writing a book chapter using historical analogies.\n"
        "### Backstory:\n"
        "You are a master storyteller and a historian of technology and science. You have an "
        "uncanny ability to find the perfect analogy from the past to illuminate a complex "
        "modern idea. Your writing is engaging, rich with detail, and always serves to "
        "clarify the core argument by showing how history repeats itself.\n\n"
        "### Chapter Assignment:" # Inputs will be prepended by Runner.run
    ),
    model=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the default from settings
    output_type=StringOutput, # Expecting raw text chapter content
)
# --- Agent Instances Map ---
# Update AGENT_INSTANCES to include the new agent
AGENT_INSTANCES = {
    "Architect Part AI": architect_part_agent,
    "Architect Chapter AI": architect_chapter_agent, # NEW ADDITION
    "Continuity Editor AI": continuity_editor_agent,
    "Historian AI": historian_agent,
    "Technologist AI": technologist_agent,
    "Philosopher AI": philosopher_agent,
    "Theorist AI": theorist_agent,
}
