from pydantic import BaseModel,Field
from typing import List
from langchain_core.output_parsers import PydanticOutputParser

class InterviewQues(BaseModel):
    categories : List[str] = Field(description="Each Values Stores the Category of a question.")
    questions : List[str] = Field(description="Each Values Stores a question of its corresponding category in previous list.")

parser = PydanticOutputParser(pydantic_object=InterviewQues)

format_instructions = parser.get_format_instructions()