from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

class InterviewQues(BaseModel):
    categories: List[str] = Field(
        description="Each Values Stores the Category of a question."
    )
    questions: List[str] = Field(
        description="Each Values Stores a question of its corresponding category in previous list."
    )


parser1 = PydanticOutputParser(pydantic_object=InterviewQues)

format_instructions1 = parser1.get_format_instructions()



class ResumeAchievements(BaseModel):
    certifications: List[str]
    issuing_authority: List[str]
    certificate_links: List[str]
    date_earned:datetime
    platform_links: List[str]

parser2 = PydanticOutputParser(pydantic_object=ResumeAchievements)
format_instructions2 = parser2.get_format_instructions()