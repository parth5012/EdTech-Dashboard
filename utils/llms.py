from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from utils.prompt import prompt_extract,analyser_prompt,readiness_prompt,interview_prompt
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite',api_key = os.getenv('GEMINI_API_KEY'))
def get_resume_content(resume):
    if resume.endswith('.pdf'):
        loader = PyPDFLoader(resume)
        content = loader.load()
    
    if resume.endswith('.docx'):
        loader = Docx2txtLoader(resume)
        content = loader.load()
    
    resume_content = ''
    for i in range(len(content)):
        resume_content += content[i].page_content
    return resume_content

def get_json_output(resume_content):
    chain = prompt_extract | llm | JsonOutputParser()
    res =chain.invoke({"resume_data": resume_content})
    print(res)
    
    return res
    


def get_str_output(resume_content):
    chain = analyser_prompt | llm | StrOutputParser()
    return chain.invoke(resume_content)

def get_readiness_score(resume_content):
    chain = readiness_prompt | llm | StrOutputParser()
    return chain.invoke(resume_content)


def get_interview_ques(job_desc):
    chain = interview_prompt | llm | JsonOutputParser()
    return chain.invoke(job_desc['interview_questions'])
