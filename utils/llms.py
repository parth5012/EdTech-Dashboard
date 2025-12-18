from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from utils.prompt import (
    prompt_extract,
    analyser_prompt,
    readiness_prompt,
    interview_prompt,
    check_prompt,
    ats_prompt,
    cover_letter_prompt,
    job_details_prompt,
)
from langchain_core.runnables import RunnableLambda, RunnableParallel
import os
from dotenv import load_dotenv
from langsmith import traceable
from utils.output_models import parser1, parser2, InterviewQues, ResumeAchievements
from typing import List
# from utils.graphs import ATS,JobDetails

load_dotenv()

llm1 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", api_key=os.getenv("GEMINI_API_KEY")
)
llm2 = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)


@traceable(name="Resume Reader")
def get_resume_content(resume: __file__) -> str:
    content = []
    if resume.endswith(".pdf"):
        loader = PyPDFLoader(resume)
        content = loader.load()
    elif resume.endswith(".docx"):
        loader = Docx2txtLoader(resume)
        content = loader.load()

    resume_content = ""
    for page in content:
        resume_content += page.page_content
    return resume_content


@traceable(name="Extracting Details From Resume")
def get_achievements(resume_content: str) -> ResumeAchievements:
    chain = prompt_extract | llm1 | parser2
    res = chain.invoke({"resume_data": resume_content})
    print(res)

    return res


@traceable(name="Improvement One Liners")
def get_str_output(resume_content: str) -> List[str]:
    chain = analyser_prompt | llm1 | StrOutputParser()
    return chain.invoke(resume_content)


@traceable(name="Readiness Score")
def get_readiness_score(resume_content: str) -> str:
    chain = readiness_prompt | llm1 | StrOutputParser()
    return chain.invoke(resume_content)


@traceable(name="Generate Interview Ques")
def get_interview_ques(job_desc: str) -> InterviewQues:
    chain = interview_prompt | llm2 | parser1
    res = chain.invoke(job_desc)
    print(res)
    return res


@traceable(name="Check Answer")
def is_answer(ques: str, answer: str) -> bool:
    chain = check_prompt | llm1 | StrOutputParser()
    res = chain.invoke({"ques": ques, "ans": answer})
    return bool(res)


@traceable(name="ATS score")
def get_ats_score(resume_content: str, job_desc: str) -> dict:
    process_inputs = RunnableParallel(
        jd_text=RunnableLambda(lambda x: x["jd_text"]),
        resume_text=RunnableLambda(lambda x: x["resume_text"]),
    )
    chain = process_inputs | ats_prompt | llm1 | StrOutputParser() | JsonOutputParser()
    return chain.invoke({"jd_text": job_desc, "resume_text": resume_content})


@traceable(name="Cover Letter")
def generate_cover_letter(resume_content: str, job_desc: str) -> str:
    process_inputs = RunnableParallel(
        job_desc=RunnableLambda(lambda x: x["job_desc"]),
        resume=RunnableLambda(lambda x: x["resume"]),
    )
    chain = (
        process_inputs
        | cover_letter_prompt
        | llm1
        | StrOutputParser()
        | JsonOutputParser()
    )
    return chain.invoke({"job_desc": job_desc, "resume": resume_content})


@traceable(name="Fetch Job Details")
def get_job_details(job_desc: str) -> dict:
    chain = job_details_prompt | llm1 | JsonOutputParser()
    return chain.invoke(job_desc)
