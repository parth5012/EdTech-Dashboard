from langchain_core.prompts import PromptTemplate

prompt_extract = PromptTemplate.from_template(
        """
        ### SCRAPED TEXT FROM RESUME:
        {resume_data}
        ### INSTRUCTION:
        The scraped text is from the Resume of a candidate looking for jobs.
        Your job is to extract the content of this resume and return them in JSON format containing the 
        following keys: `certification name`, `issuing authority`, `date earned` and `coding platforms profile links` .
        Only return the valid JSON. Store multiple records of a key in form of list.
        ### VALID JSON (NO PREAMBLE):    
        """)

analyser_prompt = PromptTemplate.from_template('''You are a senior technical recruiter, skilled at 10-second resume reviews.

Analyze the resume below, which is for a candidate targeting a technical role.

Provide only one  concise, **one-liner** improvement recommendations for the candidate. These should be short, actionable tips, exactly like the examples below.

Examples of desired format:
* “Quantify your project achievements.”
* “Add a dedicated 'Technical Skills' section.”
* “Tailor your summary to the job description.”
* “Improve focus on SQL and data visualization.”

Resume Content:
{resume_content}''')