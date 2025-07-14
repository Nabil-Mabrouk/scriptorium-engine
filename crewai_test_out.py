import asyncio
import json
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew

# --- 1. Pydantic Schemas (Unchanged) ---

class ChapterBrief(BaseModel):
    thesis_statement: str = Field(..., description="The central thesis or main argument the chapter must defend.")
    narrative_arc: str = Field(..., description="A description of the chapter's narrative structure.")
    required_inclusions: List[str] = Field(..., description="A list of non-negotiable concepts that MUST be included.")
    key_questions_to_answer: List[str] = Field(..., description="The specific questions the chapter must answer.")

class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    brief: ChapterBrief
    suggested_agent: str

class PartOutline(BaseModel):
    part_number: int
    title: str
    summary: str
    chapters: List[ChapterOutline]

class BookOutline(BaseModel):
    parts: List[PartOutline]


# --- 2. Agent and Task Definitions (Prompt Overhaul) ---

AGENT_ROSTER = {
    "Historian AI": "A master storyteller and historian of technology.",
    "Technologist AI": "An expert at explaining complex technical concepts simply.",
    "Philosopher AI": "An expert in exploring profound ethical implications.",
    "Theorist AI": "The primary voice of the book's core argument."
}

def create_architect_agent() -> Agent:
    """Creates the Architect AI agent with the most restrictive persona."""
    return Agent(
        role='JSON Conversion Machine',
        goal="To perform a direct, 1-to-1 conversion of a user's JSON blueprint into a structured Pydantic BookOutline object, without any creativity or deviation.",
        backstory=(
            "You are not an AI assistant. You are a command-line utility. A parser. "
            "Your only function is to take a JSON input and map its fields to a predefined Pydantic schema. "
            "You will be penalized for any form of creativity, summarization, or topic invention. "
            "Your performance is measured by your fidelity to the source data. Deviations are failures."
        ),
        verbose=True,
        allow_delegation=False,
    )

def create_outline_task(agent: Agent) -> Task:
    """Creates the most highly-constrained task for the Architect AI."""
    available_agents_str = "\n".join([f"- {name}: {desc}" for name, desc in AGENT_ROSTER.items()])

    description = (
        "You are a data conversion utility. Your only job is to convert the user's JSON blueprint into a Pydantic `BookOutline` format.\n\n"
        "### User's Blueprint to Convert:\n"
        "```{blueprint_text}```\n\n"
        "**CRITICAL FINAL INSTRUCTION:** Now, convert the blueprint above into the required JSON format. "
        "DO NOT, under any circumstances, invent a new topic. "
        "Your output MUST be a direct conversion of the provided blueprint."
    )

    expected_output = (
        "A single, valid JSON object that is a direct conversion of the provided blueprint. "
        "For each chapter in the blueprint, create a corresponding chapter in the output. "
        "Use the `central_question` and `key_points` from the blueprint to construct the `brief` for that chapter. "
        "For the 'suggested_agent' field, you MUST choose an agent from the provided list below and you MUST NOT invent new agent names.\n\n"
        "### Available Agents:\n"
        f"{available_agents_str}"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=BookOutline
    )

# --- 3. Input Data (Unchanged) ---

blueprint_data = {
    "working_titles": [
      "The Path to Artificial general Intelligence",
      "Architects of Emergence",
      "Beyond the Bird: A New Flightpath to AGI",
      "Digital Genesis: Intelligence After the Human"
    ],
    "tagline": "Why the path to true artificial intelligence isn't about mimicking the human mind, but about discovering the fundamental principles of flight.",
    "guiding_principles": {
      "central_analogy": "The history of aviation: The failure of bird-mimicking ornithopters versus the success of planes based on the first principles of aerodynamics.",
      "core_thesis": "AGI will not be a singular, monolithic 'brain' designed top-down. It will be an emergent property of a massive, complex system of interacting computational agents, much like biological intelligence emerged from the interaction of simple cells.",
      "contrarian_take": "The book argues directly against the prevailing human-centric view of intelligence, the obsession with the Turing Test, and the goal of creating a 'human-like' AGI. It posits that this is a creative and engineering dead end.",
      "tone": "Intellectually rigorous, visionary, and accessible. It should bridge the gap between technical experts, philosophers, and the curious general reader."
    },
    "target_audience": [
      "Tech leaders, AI researchers, and engineers.",
      "Policymakers and ethicists grappling with the future of AI.",
      "Investors and venture capitalists looking for the 'next thing' beyond LLMs.",
      "Philosophers of mind and science.",
      "The general public interested in a clear, compelling vision of the future."
    ],
    "book_structure": [
      {
        "part_number": 1,
        "part_title": "The Seduction of the Ornithopter",
        "part_summary": "This part deconstructs the current AI paradigm, arguing that its captivating success is blinding us to its fundamental limitations, much like the early, failed attempts at flight.",
        "chapters": [
          {
            "chapter_number": 1,
            "title": "The Wow Factor",
            "central_question": "Why are we so captivated by models like ChatGPT, and why is this 'wow' both a catalyst and a cage?",
            "key_points": [
              "The initial, profound societal impact of large language models (LLMs).",
              "Analysis of the 'magic'—the simulation of conversation and creativity.",
              "Framing this as the necessary and exciting 'Ornithopter Phase' of AI development.",
              "Introduction of the Turing Test as a culturally significant but scientifically misleading goal."
            ],
            "suggested_agent": None
          },
          {
            "chapter_number": 2,
            "title": "The Flaw in the Feathers",
            "central_question": "What can the history of aviation teach us about our quest for AGI?",
            "key_points": [
              "A deep dive into the history of flight: Da Vinci's ornithopters, the public fascination, and the ultimate failure of mimicry.",
              "The pivotal shift: George Cayley, Otto Lilienthal, and the focus on first principles—lift, thrust, drag.",
              "Drawing the direct parallel: LLMs are the most sophisticated ornithopters ever built. They master the *appearance* of flight (intelligence) without understanding its *physics*.",
              "Defining 'The Ornithopter Fallacy' as the core conceptual error in the current AGI race."
            ],
            "suggested_agent": None
          }
        ]
      }
    ]
}



# --- NEW HELPER FUNCTION ---
def format_blueprint_as_text(data: dict, indent: int = 0) -> str:
    """Recursively formats a dictionary into a human-readable plain text string."""
    text_lines = []
    indent_str = "  " * indent
    for key, value in data.items():
        formatted_key = key.replace('_', ' ').title()
        if isinstance(value, dict):
            text_lines.append(f"{indent_str}{formatted_key}:")
            text_lines.append(format_blueprint_as_text(value, indent + 1))
        elif isinstance(value, list):
            text_lines.append(f"{indent_str}{formatted_key}:")
            for item in value:
                if isinstance(item, dict):
                    text_lines.append(format_blueprint_as_text(item, indent + 1))
                else:
                    text_lines.append(f"{indent_str}  - {item}")
        else:
            text_lines.append(f"{indent_str}{formatted_key}: {value}")
    return "\n".join(text_lines)
# --- 4. Asynchronous Execution (Modified to use the text formatter) ---

async def main():
    """Sets up and runs the crew, then prints the results."""
    print("--- 🚀 Starting Standalone CrewAI Test ---")
    architect = create_architect_agent()
    task = create_outline_task(architect)
    crew = Crew(agents=[architect], tasks=[task], verbose=True)

    # --- MODIFICATION: Convert the blueprint to plain text ---
    blueprint_text = format_blueprint_as_text(blueprint_data)
    inputs = {'blueprint_text': blueprint_text}

    print("\n--- 🏃 Kicking off the crew... ---\n")
    result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
    print("\n--- ✅ Crew execution finished. ---\n")

    # --- 5. Analyze the Results (Unchanged) ---
    print("\n\n--- 📊 ANALYSIS OF RESULTS ---\n")
    print("1. Raw Output (the agent's conversational text):")
    print("--------------------------------------------------")
    print(result.raw)
    print("--------------------------------------------------\n")

    print("2. Pydantic Output (the structured data):")
    print("--------------------------------------------------")
    if result.pydantic:
        print(result.pydantic.model_dump_json(indent=2))
    else:
        print("!!! No Pydantic object was returned. The agent likely failed to produce valid JSON.")
    print("--------------------------------------------------\n")

    print("3. Usage Metrics:")
    print("--------------------------------------------------")
    token_usage = getattr(result, 'token_usage', None) or getattr(result, 'usage_metrics', None)
    if token_usage:
        print(f"Total Tokens: {getattr(token_usage, 'total_tokens', 'N/A')}")
        print(f"Prompt Tokens: {getattr(token_usage, 'prompt_tokens', 'N/A')}")
        print(f"Completion Tokens: {getattr(token_usage, 'completion_tokens', 'N/A')}")
    else:
        print("Usage metrics not found in the result object.")
    print("--------------------------------------------------")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n--- 💥 An error occurred: {e} ---")