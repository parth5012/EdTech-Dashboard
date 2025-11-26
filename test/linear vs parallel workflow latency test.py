from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
from utils.llms import get_str_output,get_readiness_score,get_interview_ques
import time
from typing import TypedDict,List

job_desc='''Job Title: Junior Data Scientist
Location: [City, State] Position Type: Full-Time, Entry-Level

Company Overview
[Brief, 1-2 sentence description of your company, its mission, and the problems you are solving. Example: "At [Company Name], we are a fast-growing tech firm dedicated to revolutionizing [Your Industry] through data-driven insights. We believe in the power of data to shape products, strategies, and user experiences."]

Job Summary
We are looking for a motivated and curious Junior Data Scientist to join our dynamic analytics team. This is an ideal role for a recent graduate or early-career professional passionate about turning large datasets into actionable insights. You will work closely with senior data scientists, engineers, and product managers to tackle challenging problems, from data collection and cleaning to building and deploying machine learning models.

Core Responsibilities
Data Collection & Cleaning: Assist in gathering data from various sources (SQL databases, APIs, flat files) and perform necessary preprocessing and cleaning to ensure data quality and integrity.

Exploratory Data Analysis (EDA): Analyze data to identify trends, patterns, and anomalies. Use statistical methods to uncover insights and formulate hypotheses.

Model Building & Validation: Apply fundamental machine learning algorithms (e.g., regression, classification, clustering) to build predictive models. You will be responsible for training, testing, and validating these models.

Data Visualization: Create compelling reports and dashboards using tools like Tableau, Power BI, or Python libraries (Matplotlib, Seaborn) to communicate your findings to both technical and non-technical stakeholders.

Collaboration: Work collaboratively with cross-functional teams to understand business requirements and deliver data-driven solutions that meet their needs.

Qualifications & Skills
Required:
Educational Background: A Bachelor's or Master's degree in Data Science, Computer Science, Statistics, Mathematics, Economics, or another related quantitative field.

Technical Skills:

Strong proficiency in Python and its data science ecosystem (pandas, NumPy, scikit-learn).

Solid understanding of SQL for data querying and manipulation.

Familiarity with data visualization libraries (e.g., Matplotlib, Seaborn) or BI tools (e.g., Tableau, Power BI).

Knowledge Base:

A firm grasp of core statistical concepts and machine learning fundamentals (supervised vs. unsupervised learning, model evaluation metrics, etc.).

Soft Skills:

Excellent problem-solving and analytical abilities.

Strong communication skills, with the ability to explain complex technical concepts to a non-technical audience.

A natural curiosity and a strong desire to learn.

Preferred (Nice to Have):
Prior internship experience in a data-related role (data analyst, data scientist, etc.).

A portfolio of data science projects (e.g., on GitHub) that showcases your skills and passion.

Experience with cloud platforms (AWS, GCP, or Azure).

Familiarity with version control (Git).

Basic understanding of deep learning frameworks (e.g., TensorFlow, PyTorch).'''
resume_content ="Hayden Smith   \n214 Mitre Avenue, Park Hill, 3045 |  04501 123 456  |  haydensmith@email.com  \n  \n(Tip: Name, mobile number and email address are essential. Current address could be included \nespecially if you live nearby. Ensure that it is clearly displayed)  \nhttps://leetcode.com/u/HLHWTbXcl7/ \nhttps://www.naukri.com/code360/profile/30fc2a8a-aace-4817-8f6c-6f867680fbe4    \nCareer Objective   \nI am reliable hard working Year 11 student seeking casual or part-time customer service work in a \nsports retail environment. Having played soccer for nine years and a keen all-round sports \nenthusiast, I am looking to contribute knowledge and proven communications skills.   \n  \n(Tip: A career objective isn’t essential, but it’s useful if you don't have much experience and can \nconvey enthusiasm and motivation. Briefly summarise any work you have done, your strengths and \nrelevant expertise and state how you aim to apply this to your career goal. Adjust the statement to \nreflect the role you are applying for.)    \nAvailability  \nMonday – Friday: 4.30pm – 10.00pm  \nSaturday – Sunday: 8.00am – 11.00pm  \n(up to 20 hours per week)  \n  \n(Tip: When looking for part-time casual work, it can be a good idea to include availability. If you’re a \nstudent, clearly state the maximum number of hours you are able to work per week.) Key Skills  \n• Customer service ability demonstrated when working efficiently in soccer club canteen.  \n• Numeracy skills for cash handling tasks proven by achieving good results for mathematics \nsubjects.   \n• Highly developed communication skills shown by receiving positive feedback from \nsupervisors after completing work experience.   \n• Strong ability to work as part of a team developed through participating in soccer since the \nage of eight.  \n• Demonstrated organisation skills as a result handing all assignments in on time.  \n• Able to take responsibility and solve problems proven through umpiring and coaching.   \n  \n (Tip: Include 5-9 key skills as bullet points that you like using and that are relevant to the role. When \napplying for advertised roles, match to any criteria listed in the advertisement. Use action words such \nas ‘demonstrated’ or ‘highly developed’ and then provide information about when, where and how \nyou’ve used the skill through your studies, work experience, volunteering, sporting activities, etc.)  \nEducation  \nCurrent     \nPark Hill Secondary College    Year 11  \n •  Subjects include: Maths, English, Business Management, VET studies in Sport and  \n  Recreation.(Tip: List your most recent education qualifications first including any relevant university degrees and \ncertificates. Professional development such as short training courses, workshops, licences, forms of \naccreditation, and other training can be included but is usually a separate heading.)  \nWork Experience   \nPage 1  \n  \n    Hayden Smith  \nDecember 2016 – March 2017  \nPark Hill Soccer Club Canteen    Customer service (volunteer)  \n• Served customers.  \n• Handled cash including operating of cash register.  \n  \nJune 2016 – February 2017  \nArgo Newsagency      Newspaper deliverer  \n •  Delivered weekend newspapers to houses.  \n  \n(Tip: Focus on most recent work experience first. Include your job title, organisation name and dates.  \nYears and months can be included. Include responsibilities and achievements for each role.)  \nLeadership Roles   \n2016 – current         \nSoccer umpire for under 14 team  Park Hill Soccer Club  \n  \n2017 – current         \nAssistant Coach for junior players  Park Hill Soccer Club  \n  \n(Tip: Include any volunteering, community participation or leaderships roles.)  \nInterests/Hobbies  \n• Played soccer since the age of eight.  \n• Keen spectator of soccer, football and cricket.  \n  \n(Tip: Including a section on interests can be useful if it’s relevant and active. Only include those \ninterests which are relevant to the job you are applying for or those which demonstrate your \nproactive or positive traits.)       \nReferees  \nJohn Charles  \nCoach  \nHill Park Soccer Club 0456 \n789 101  \nWendy Stevens  \nYear 11 Coordinator  \nHill Park Secondary College  \n*Contact details available on request  \nJohn_charles@hillpark.edu  \n  \n(Tip: If you decide to include referee contacts, notify the referee and indicate the type of roles that \nyou will be applying for. You may also want to provide them with a copy of your resume. You can also \nsimply write ‘Available on request’.)  \nPage 2  \n Certifications \n    Introduction to GenAI by Google CloudIntroduction to Prompt Engineering my NVIDIA"


print("linear execution")
start = time.time()
get_interview_ques(job_desc)
get_readiness_score(resume_content)
get_str_output(resume_content)
end = time.time()
exec_time = end-start
print(f'Execution time : {exec_time:.2f} seconds')


# Parallel flow
class QuestionCategory(TypedDict):
    category:str
    questions:List[str]
class EdTechState(TypedDict):
    job_desc:str
    resume_content:str
    ques : List[QuestionCategory]
    readiness_score:float
    analysis_quote: str

def interview_ques(state:EdTechState):
    job_desc = state['job_desc']
    ques = get_interview_ques(job_desc)
    return {'ques':ques}

def readiness_score(state:EdTechState):
    content = state['resume_content']
    score = get_readiness_score(content)
    return {'readiness_score':score}

def analysis(state:EdTechState):
    content = state['resume_content']
    quote = get_str_output(content)
    return {'analysis_quote':quote}

start=time.time()
graph = StateGraph(EdTechState)

graph.add_node('interview_ques',interview_ques)
graph.add_node('score',readiness_score)
graph.add_node('quote',analysis)

graph.add_edge(START,'interview_ques')
graph.add_edge(START,'score')
graph.add_edge(START,'quote')

graph.add_edge('interview_ques',END)
graph.add_edge('score',END)
graph.add_edge('quote',END)

workflow = graph.compile()


print('Parallel Workflow')
output_state = workflow.invoke({'job_desc':job_desc,
                                'resume_content':resume_content})
end = time.time()

exec_time = end-start
print(f'Execution time : {exec_time:.2f} seconds')