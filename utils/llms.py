from langchain_google_genai import ChatGoogleGenerativeAI
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

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", api_key=os.getenv("GEMINI_API_KEY")
)

@traceable(name="Resume Reader")
def get_resume_content(resume):
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
def get_json_output(resume_content):
    chain = prompt_extract | llm | JsonOutputParser()
    res = chain.invoke({"resume_data": resume_content})
    print(res)

    return res

@traceable(name="Improvement One Liners")
def get_str_output(resume_content):
    chain = analyser_prompt | llm | StrOutputParser()
    return chain.invoke(resume_content)

@traceable(name="Readiness Score")
def get_readiness_score(resume_content):
    chain = readiness_prompt | llm | StrOutputParser()
    return chain.invoke(resume_content)

@traceable(name="Generate Interview Ques")
def get_interview_ques(job_desc):
    chain = interview_prompt | llm | JsonOutputParser()
    res = chain.invoke(job_desc)
    print(res)
    return res["interview_questions"]

@traceable(name="Check Answer")
def is_answer(ques, answer):
    chain = check_prompt | llm | StrOutputParser()
    res = chain.invoke({"ques": ques, "ans": answer})
    return res

@traceable(name="ATS score")
def get_ats_score(resume_content, job_desc):
    process_inputs = RunnableParallel(
        jd_text=RunnableLambda(lambda x: x["jd_text"]),
        resume_text=RunnableLambda(lambda x: x["resume_text"]),
    )
    chain = process_inputs | ats_prompt | llm | StrOutputParser() | JsonOutputParser()
    return chain.invoke({"jd_text": job_desc, "resume_text": resume_content})

@traceable(name="Cover Letter")
def generate_cover_letter(resume_content, job_desc):
    process_inputs = RunnableParallel(
        job_desc=RunnableLambda(lambda x: x["job_desc"]),
        resume=RunnableLambda(lambda x: x["resume"]),
    )
    chain = (
        process_inputs
        | cover_letter_prompt
        | llm
        | StrOutputParser()
        | JsonOutputParser()
    )
    return chain.invoke({"job_desc": job_desc, "resume": resume_content})

@traceable(name="Fetch Job Details")
def get_job_details(job_desc):
    chain = job_details_prompt | llm | JsonOutputParser()
    return chain.invoke(job_desc)
