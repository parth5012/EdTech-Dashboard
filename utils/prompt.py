from langchain_core.prompts import PromptTemplate

prompt_extract = PromptTemplate(template="""
        ### SCRAPED TEXT FROM RESUME:
        {resume_data}
        ### INSTRUCTION:
        The scraped text is from the Resume of a candidate looking for jobs.
        Your job is to extract the content of this resume and return them in JSON format containing the 
        following keys: `certifications`,`certificate links`, `issuing authority`, `date earned` and `platform link` . platform link refers to the platforms used to practice coding like code360,leetcode,hackersrank,github ,etc.
        Only return the valid JSON. Store records of a key in form of list always.if a key has multiple values store those values in the form of a list .
        Refer to the Example :
       " {{'certifications': [certificate1,certificate2,certificate3],
        'issuing authority': [Company1,Company2,Company3],
        'date earned': [date1, date2,date3],
 'platform link': [link1,link2,link]}}"
        ### VALID JSON (NO PREAMBLE):    
        """,input_variables=['resume_data'])

analyser_prompt = PromptTemplate.from_template('''You are a senior technical recruiter, skilled at 10-second resume reviews.

Analyze the resume below, which is for a candidate targeting a technical role.

Provide only three  concise, **one-liner** improvement recommendations for the candidate. These should be short, actionable tips, exactly like the examples below.

Examples of desired format:
* “Quantify your project achievements.”
* “Add a dedicated 'Technical Skills' section.”
* “Tailor your summary to the job description.”
* “Improve focus on SQL and data visualization.”

Resume Content:
{resume_content}''')


readiness_prompt = PromptTemplate.from_template('''You are a senior technical recruiter with deep experience in evaluating resumes for software engineering, data science, and other technical roles.

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
        ''')