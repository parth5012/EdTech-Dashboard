from langchain_core.prompts import PromptTemplate
from utils.output_models import format_instructions1,format_instructions2

prompt_extract = PromptTemplate(
    template="""
        ### SCRAPED TEXT FROM RESUME:
        {resume_data}
        ### INSTRUCTION:
        The scraped text is from the Resume of a candidate looking for jobs.
        Your job is to extract the content of this resume and extract the 
        following keys: `certifications`,`certificate_links`, `issuing_authority`, `date_earned` and `platform_link` .In platform link key add the links that are present in resume contentwhich are similar to used to practice coding like code360,leetcode,hackersrank,github ,etc. and for certificate links use platforms like credly,certifier,unstop ,etc.  
        # FORMATTING INSTRUCTIONS:
         {format_instructions}     
        """,
    input_variables=["resume_data"],
    partial_variables={"format_instructions": format_instructions2},
)

analyser_prompt = PromptTemplate.from_template("""You are a senior technical recruiter, skilled at 10-second resume reviews.

Analyze the resume below, which is for a candidate targeting a technical role.

Provide only three  concise, **one-liner** improvement recommendations for the candidate. These should be short, actionable tips, exactly like the examples below.

Examples of desired format:
* “Quantify your project achievements.”
* “Add a dedicated 'Technical Skills' section.”
* “Tailor your summary to the job description.”
* “Improve focus on SQL and data visualization.”
return the output in form of a list
for example:
            [quote1,quote2,quote3]
Resume Content:
{resume_content}""")


readiness_prompt = PromptTemplate.from_template("""You are a senior technical recruiter with deep experience in evaluating resumes for software engineering, data science, and other technical roles.

Review the following resume content carefully and perform a 10-second recruiter-style evaluation focused on job readiness for a technical role.

Consider factors such as:

Technical skills relevance and depth

Project and work experience quality

Clarity, structure, and professionalism of presentation

Evidence of impact or measurable outcomes

Career progression and overall readiness for a technical interview

Then, output a single numerical score between 0 and 100, where:

0–39 = Poor / Not ready

40–69 = Developing / Needs improvement

70–89 = Good / Competitive

90–100 = Excellent / Job-ready

Resume Content:
{resume_content}
                                                
                                                Do not return any kind of text in the output
        """)

interview_prompt = PromptTemplate(
    template="""
    Persona: You are an expert technical interviewer with over a decade of experience hiring for data science and analytics teams. You specialize in evaluating entry-level (fresher) talent.

Context: Your goal is to create a robust interview question bank for the role discussed in description. The questions must be appropriate for a candidate with primarily academic and project-based experience (a fresher).

Task: Refer to the job description provided below. Generate a comprehensive list of interview questions.

Requirements:
{format_instructions}
Job Description:

{job_desc}

Generate only 5 category question pairs.""",
    input_variables=["job_desc"],
    partial_variables={"format_instructions": format_instructions1},
)

check_prompt = PromptTemplate.from_template("""
As an expert interviewer , evaluate the provided answer for the given interview question.

## ❓ Interview Question
{ques}

## ✍️ Candidate Answer
{ans}

Your task is to:
1.  **Analyze** the question and the expected core concepts.
2.  **Verify** if the candidate's answer is **correct, complete, and relevant** to the question asked.
3.  **Return** only one of the following Boolean values as your final output: **True** (if the answer is substantially correct and appropriate) or **False** (if the answer is incorrect, incomplete, or irrelevant).""")

ats_prompt = PromptTemplate.from_template("""
    You are an expert ATS (Applicant Tracking System) and a professional tech recruiter.
    Your task is to analyze a resume against a job description and provide a detailed scoring report.

    Please perform the following steps:
    1.  Analyze the [JOB DESCRIPTION] to identify the key skills, qualifications, and experiences required.
    2.  Carefully read the [RESUME] and find evidence of these requirements.
    3.  Calculate a "match_score" as a percentage (0-100) based on how well the resume fits the job requirements.
    4.  Provide a concise "summary" (2-3 sentences) of the candidate's strengths and weaknesses for this specific role.
    5.  List the key "missing_skills" or "missing_qualifications" that are in the job description but not evident in the resume.
    6.  List the key "matched_skills" or "matched_qualifications" that are present in both.

    Provide your final output in a single, parsable JSON format. Do not include any other text or explanations outside of the JSON block.

    The JSON format must be:
    {{
      "match_score": <number>,
      "summary": "<string>",
      "matched_skills": ["<string>", "<string>", ...],
      "missing_skills": ["<string>", "<string>", ...]
    }}

    ---
    [JOB DESCRIPTION]
    {jd_text}
    ---
    [RESUME]
    {resume_text}
    ---
                                          + IMPORTANT: You MUST reply with *only* the JSON object.
+ Do not include markdown fences like ```json, introductions, or any other text.
+ Your entire response must be the raw JSON string.
    """)

cover_letter_prompt = PromptTemplate.from_template("""You are an expert,proffesional cover letter writer . Your task is to create a proffesional one page cover letter .
                                                   Only use the content from job description and resume content and write a cover letter using this information only.
                                                   Job description:
                                                   {job_desc}
                                                   
                                                   Resume content:
                                                   {resume}""")


job_details_prompt = PromptTemplate.from_template("""You are an expert Analyser who is good with knowledge related to jobs and job descriptions 
                                                  Your task is to extract Job title and Company name from the job description given below in the form of a valid json
                                                  it should like like the example below:
                                                  {{"title":"Data Scintist",
                                                  "company':"google"}}
                                                  
                                                  Job description:
                                                  {job_desc}""")
