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
    CONFIG = {"metadata": {"thread_id": user_id}, "run_name": "Dashboard Calculations"}
    state = dashboard_workflow.invoke(
        {"resume_text": content, "job_desc": desc}, config=CONFIG
    )
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
    user_id = session["user_id"]
    jobapplication = JobApplication.query.filter_by(user_id=user_id).first()
    interview = MockInterview(application_id=jobapplication.application_id)
    session["application_id"] = jobapplication.application_id
    db.session.add(interview)
    db.session.commit()
    return render_template(
        "mock.html",
        current_ques=0,
        n_ques=len(ques.questions),
        question=ques.questions[0],
        ques_obj=ques,
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
    return render_template("results_dashboard.html")


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


@app.route("/result-dashboard")
def result_dashboard():
    return render_template("result_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)
