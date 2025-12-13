from flask import render_template, request, redirect, url_for, session, jsonify, flash
import os
from werkzeug.utils import secure_filename
from utils.llms import (
    get_resume_content,
    is_answer,
    get_interview_ques,
)
from utils.stats import get_performance_score
from utils.verification import verify_public_badge
from utils.answer import get_transcription

# from utils.ats import calculate_ats_score
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from dotenv import load_dotenv
from utils.test_cases import call_gemini_api
from utils.app import app, db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.models import (
    InterviewAnswer,
    InterviewQuestion,
    MockInterview,
    User,
    JobApplication,
    JobDescription,
    Resume,
)
from utils.graphs import dashboard_workflow


load_dotenv()
dsn = os.getenv("DSN")

sentry_sdk.init(
    dsn=dsn,
    integrations=[
        FlaskIntegration(),
    ],
    traces_sample_rate=1.0,
)

resume_path = 0
user_answers = {}

uri = os.getenv("URI")
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "connect_args": {"sslmode": "require", "connect_timeout": 10},
}
# db.init_app(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        # retrieving all emails
        emails = db.session.query(User.email).all()
        email_list = [email[0] for email in emails]
        print(email_list)
        if email in email_list:
            flash("Email already exists!!")
            return redirect("/login")
        password = request.form["password"]

        # Hash password using Werkzeug
        hashed_password = generate_password_hash(password)

        new_user = User(name=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")


# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        session["user"] = user
        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            return redirect("/user_dashboard")
        else:
            return "Invalid email or password"

    return render_template("login.html")


@app.route("/user_dashboard")
def user_dashboard():
    return render_template("user_dashboard.html")


@app.route("/upload_resume", methods=["post"])
def upload_resume():
    if request.method == "POST":
        resume = request.files["resume"]
        filename = secure_filename(resume.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        desc = request.form["job_description"]
        session["desc"] = desc
        resume.save(filepath)
        content = get_resume_content(filepath)
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect(url_for("signup"))
        session["user_id"] = user.id
        # resume_path = filepath
        resume = Resume(user_id=user.id, resume_text=content)
        # if os.path.exists(filepath):
        #     os.remove(filepath)
        # session["desc"] = desc
        db.session.add(resume)
        db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "desc" not in session:
        return redirect(url_for("home"))
    # user dict
    user_id = session["user_id"]
    resume = Resume.query.filter_by(user_id=user_id).first()
    content = resume.resume_text
    desc = session["desc"]
    CONFIG={
        'metadata': {'thread_id':user_id},
        'run_name': "Dashboard Calculations"
    }
    state = dashboard_workflow.invoke({"resume_text": content, "job_desc": desc},config=CONFIG)
    details = state["job_details"]
    if not details["title"]:
        return redirect(url_for("home"))
    job_desc = JobDescription(
        job_title=details["title"], company_name=details["company"], job_desc=desc
    )
    db.session.add(job_desc)
    db.session.flush()
    json_content = state["candidate_details"]
    session["content"] = json_content
    analysis_quote = state["analysis_quote"]
    readiness_score = state["readiness_score"]
    performance = 0
    # Slow since inference calls have high latency
    # ats = get_ats_score(content, session['desc'])
    # Latency Improvement
    ats = state["ats"]["match_score"]
    # ats = 25
    n_crtf = len(json_content["certifications"])
    job_application = JobApplication(
        user_id=user_id,
        resume_id=resume.resume_id,
        job_description_id=job_desc.job_description_id,
        ats_score=float(ats),
        analysis_summary=analysis_quote,
        certifications_count=n_crtf,
    )
    if json_content:
        if json_content["platform_link"]:
            performance = get_performance_score(json_content=json_content)
        job_application.query.update(values={"certifications_count": n_crtf})
    else:
        performance = None

    db.session.add(job_application)
    db.session.commit()
    return render_template(
        "analysis_dashboard.html",
        quote=analysis_quote,
        readiness_score=readiness_score,
        n_crtf=n_crtf,
        performance=performance,
        ats=ats,
    )


@app.route("/dashboard/certificates")
def certificates():
    content = session["content"]
    del session["content"]
    if content["certificate_links"]:
        list = content["certificate_links"]
        count = 0
        for i in range(len(list)):
            if verify_public_badge(list[i]):
                count += 1
    else:
        count = 0
    return render_template(
        "certificates.html",
        total_crtf=len(content["certifications"]),
        crtf_count=count,
        pending_crtf=len(content["certifications"]) - count,
        content=content,
    )


@app.route("/mock", methods=["get", "post"])
def mock_interview():
    if "desc" not in session:
        return redirect(url_for("home"))
    ques = get_interview_ques(session["desc"])
    # ques = [
    #     {
    #         "category": "Introduction & Motivation",
    #         "questions": [
    #             "Tell me about yourself and why you're interested in a Junior Data Scientist role at Google, specifically within the gReach program.",
    #             "What aspects of this role and the gReach program particularly appeal to you?",
    #             "How do you see your academic background and project experience preparing you for the responsibilities outlined in the job description?",
    #             "What are your long-term career aspirations in the field of data science and analytics?",
    #             "Describe a time you had to learn a new technical skill quickly. How did you approach it?",
    #         ],
    #     },
    #     {
    #         "category": "Data Analysis & Interpretation",
    #         "questions": [
    #             "Imagine you're given a dataset of YouTube video ad performance for a client in the telecommunications industry. What key metrics would you analyze to assess their success, and why?",
    #             "How would you approach identifying user trends from YouTube video analytics for a specific industry (e.g., finance)? What kinds of insights would you look for?",
    #             "Describe a project where you had to interpret complex data and translate it into actionable insights. What was the challenge, and what was your approach?",
    #             "If a client wants to understand why their YouTube ad campaign is underperforming, what steps would you take to diagnose the issue?",
    #             "How would you go about summarizing video analytics and trends for a specific industry to a non-technical audience?",
    #         ],
    #     },
    #     {
    #         "category": "Machine Learning & AI Concepts (Entry-Level)",
    #         "questions": [
    #             "What is the difference between supervised and unsupervised learning? Provide an example of each.",
    #             "Can you explain the concept of overfitting and underfitting in machine learning models? How might you mitigate these issues?",
    #             "What are some common evaluation metrics for classification models (e.g., accuracy, precision, recall)? When would you prioritize one over the other?",
    #             "Have you had any exposure to generative AI concepts? If so, can you briefly explain what it is and its potential applications?",
    #             "Describe a simple machine learning algorithm you are familiar with (e.g., Linear Regression, K-Means). How does it work at a high level?",
    #         ],
    #     },
    #     {
    #         "category": "Programming & Tools (Python/R, SQL)",
    #         "questions": [
    #             "Describe a project where you used Python (or R) for data analysis. What libraries did you primarily use, and for what purpose?",
    #             "Write a SQL query to find the top 5 customers who spent the most on our platform in the last quarter.",
    #             "Explain the difference between a JOIN and a UNION in SQL.",
    #             "How would you handle missing values in a dataset using Python (e.g., with Pandas)?",
    #             "Imagine you have two Pandas DataFrames. How would you merge them based on a common column?",
    #         ],
    #     },
    #     {
    #         "category": "Problem Solving & Critical Thinking",
    #         "questions": [
    #             "You're tasked with creating a proposal for a new YouTube ad campaign. What information would you gather, and how would you structure your proposal?",
    #             "How would you approach streamlining a repetitive task within a sales support process to improve productivity?",
    #             "Describe a situation where you had to collaborate with others to achieve a common goal. What was your role, and how did you contribute?",
    #             "If a client is hesitant about a particular advertising solution, how would you approach addressing their concerns?",
    #             "How do you prioritize tasks when faced with multiple urgent requests?",
    #         ],
    #     },
    #     {
    #         "category": "Business Acumen & Sales Support",
    #         "questions": [
    #             "How do you think data analysis can directly contribute to improving sales productivity?",
    #             "What does it mean to act 'like an owner' in a professional setting?",
    #             "How would you tailor a presentation to a specific client's marketing objectives?",
    #             "What are your thoughts on the role of AI in the future of advertising?",
    #             "How would you go about demonstrating the success of a video advertising campaign to a client?",
    #         ],
    #     },
    #     {
    #         "category": "Behavioral & Teamwork",
    #         "questions": [
    #             "Tell me about a time you received constructive criticism. How did you respond?",
    #             "Describe a challenging project you worked on and how you overcame the obstacles.",
    #             "How do you handle working under pressure or with tight deadlines?",
    #             "What are your strengths and weaknesses when working in a team environment?",
    #             "How do you ensure you are contributing effectively to team discussions and ideation sessions?",
    #         ],
    #     },
    # ]
    # ques = ques[:5]
    user_id = session["user_id"]
    jobapplication = JobApplication.query.filter_by(user_id=user_id).first()
    interview = MockInterview(application_id=jobapplication.application_id)
    session["application_id"] = jobapplication.application_id
    db.session.add(interview)
    db.session.commit()
    return render_template(
        "mock.html",
        current_ques=0,
        n_ques=len(ques),
        question=ques[0]["questions"][0],
        ques_list=ques,
    )


@app.route("/api/mock-interview/submit", methods=["post"])
def submit():
    if request.method == "POST":
        audio = request.files["audio"]
        ans = get_transcription(audio)
        # ans = "YO"
        ques = request.form["question"]
        # Store ans in db
        # storing in placeholder db for now
        # if "user_answers" not in session:
        #     session["user_answers"] = {}
        is_right = is_answer(ques, ans)
        # is_right = False
        user_answers[ques] = (ans, is_right)
        print(user_answers)
        return jsonify({"is_answer": is_right, "message": "Your Answer is Submitted"})


@app.route("/results")
def results():
    answers = user_answers
    application_id = session["application_id"]
    interview = MockInterview.query.filter_by(application_id=application_id).first()
    # k = question and   v-> (answer,is_right)
    for k in answers.keys():
        question = InterviewQuestion(
            interview_id=interview.interview_id, question_text=k
        )
        v = answers[k]
        db.session.add(question)
        db.session.flush()
        answer = InterviewAnswer(
            question_id=question.question_id, transcription=v[0], is_active=v[1]
        )
        db.session.add(answer)
        db.session.commit()
    return render_template("results.html", answers=answers)

@app.route("/results_dashboard")
def results_dashboard():
    return render_template('results_dashboard.html')

@app.route("/debug-sentry")
def trigger_error():
    # This will raise an exception
    division_by_zero = 1 / 0
    division_by_zero += 0
    return "This won't be reached"


@app.route("/test-llm")
def test_llm_call():
    # This will run your function, and it will
    # automatically appear in LangSmith.
    feedback = call_gemini_api()
    return feedback

@app.route('/result-dashboard')
def result_dashboard():
    return render_template('result_dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)
