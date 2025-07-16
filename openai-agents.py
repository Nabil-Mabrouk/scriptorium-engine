from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from pydantic import BaseModel,  Field
import asyncio
from typing import List
import json

class Chapter(BaseModel):
    chapter_number: int = Field(..., description="Numerical order of the part")
    title: str = Field(..., description="Title of the chaptert")
    summary: str = Field(..., description="Brief description of the chapter's contentt")

class Part(BaseModel):
    part_number: int = Field(..., description="Numerical order of the part")
    title: str = Field(..., description="Title of the part")
    summary: str = Field(..., description="Brief summary of the part's content")
    chapters: List[Chapter] = Field(..., description="List of chapters of the part of the book")

class PartList(BaseModel):
    parts: List[Part] = Field(..., description="List of book parts")


architect_agent = Agent(
    name="book outline expert",
    instructions="Provide the parts and chapters outline for this book",
    output_type=PartList,
)

async def main():
    result = await Runner.run(architect_agent, "A book about the quest for AGI in AI field")
    print(result.raw_responses)
    print(result.raw_responses[0].usage)
    print("--------------------------")
    print(json.loads(result.raw_responses[0].output[0].content[0].text)["parts"])



if __name__ == "__main__":
    asyncio.run(main())