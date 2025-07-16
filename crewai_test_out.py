import asyncio
import os
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# --- 0. Environment and LLM Setup ---
load_dotenv()

llm = ChatOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="gpt-4o-mini",
    temperature=0.0 # Set to 0 for more deterministic, structured output
)

# --- 1. Pydantic Schemas (Output Definition) ---
# We'll use the Part-based structure for this test.

class PartOnlyOutline(BaseModel):
    part_number: int = Field(..., description="The sequential number of the part, starting from 1.")
    title: str = Field(..., description="The descriptive title of the part.")
    summary: str = Field(..., description="A concise summary of the part's core theme and purpose.")

class PartListOutline(BaseModel):
    """A Pydantic model for a list of parts, without chapter details."""
    parts: List[PartOnlyOutline]


# --- 2. LangChain Implementation ---

# Create an output parser and get formatting instructions
parser = PydanticOutputParser(pydantic_object=PartListOutline)

# Create the Prompt Template, including the parser's instructions
prompt_template = ChatPromptTemplate.from_template(
    "You are a master Information Architect. Your task is to analyze the user's raw book idea "
    "and identify the primary, high-level Parts of the narrative.\n"
    "{format_instructions}\n\n"
    "### User's Raw Book Idea:\n"
    "--- START ---\n"
    "{raw_blueprint}\n"
    "--- END ---\n"
)

# --- 3. Input Data ---

raw_blueprint_text = """
A book exploring the future of Artificial General Intelligence (AGI) through the central metaphor of aviation history.
The core thesis is that the current approach to AGI, which focuses on mimicking human thought, is a modern-day "ornithopter"—a machine that perfectly imitates a bird but will never achieve true flight.
The book argues that true AGI will only be achieved by discovering the first principles of emergent intelligence.
The book should be structured in three parts.
Part 1, "The Seduction of the Ornithopter," will deconstruct the current AI paradigm.
Part 2, "The Principles of Flight," will define the alternative path forward.
Part 3, "The First True Airplane," will be a forward-looking exploration of what a true, non-human AGI could do.
"""

# --- 4. Asynchronous Execution ---

async def main():
    """Sets up and runs the LangChain chain, then prints the results."""
    print("--- 🚀 Starting Standalone LangChain Test ---")

    # Define the chain using LangChain Expression Language (LCEL)
    chain = prompt_template | llm | parser

    print("\n--- 🏃 Invoking the chain... ---\n")
    # Execute the chain with the required inputs
    result = await chain.ainvoke({
        "raw_blueprint": raw_blueprint_text,
        "format_instructions": parser.get_format_instructions(),
    })
    print("\n--- ✅ Chain execution finished. ---\n")

    # --- 5. Analyze the Results ---
    print("\n\n--- 📊 ANALYSIS OF RESULTS ---\n")

    print("1. Pydantic Output (the structured data):")
    print("--------------------------------------------------")
    if isinstance(result, PartListOutline):
        print(result.model_dump_json(indent=2))
    else:
        print("!!! The chain did not return the expected Pydantic object.")
        print("\nRaw output from chain was:")
        print(result)
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n--- 💥 An error occurred: {e} ---")