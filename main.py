from flask import render_template, request, redirect, url_for, session, jsonify, flash
import os
from werkzeug.utils import secure_filename
from utils.llms import (
    get_achievements,
    get_ats_score,
    get_job_details,
    get_readiness_score,
    get_resume_content,
    get_str_output,
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
# from utils.graphs import get_dashboard_workflow
from sqlalchemy.orm import selectinload


load_dotenv()
dsn = os.getenv("DSN")

sentry_sdk.init(
    dsn=dsn,
    integrations=[
        FlaskIntegration(),
    ],
    traces_sample_rate=1.0,
)


# uri = os.getenv("URI")
# app.config["SQLALCHEMY_DATABASE_URI"] = uri
# app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
#     "pool_pre_ping": True,  # Verify connections before using them
#     "pool_recycle": 300,  # Recycle connections after 5 minutes
#     "connect_args": {"sslmode": "require", "connect_timeout": 10},
# }
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
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect("/user_dashboard")
        else:
            return "Invalid email or password"

    return render_template("login.html")


@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    apps = (
        JobApplication.query.filter_by(user_id=user_id)
        .order_by(JobApplication.created_at.asc())
        .all()
    )
    latest_app = apps[-1] if apps else None

    avg_readiness = (sum(a.ats_score for a in apps) / len(apps)) if apps else 0
    latest_ats = latest_app.ats_score if latest_app else 0
    certifications = latest_app.certifications_count if latest_app else 0

    app_ids = [a.application_id for a in apps]
    interviews = (
        MockInterview.query.filter(MockInterview.application_id.in_(app_ids)).all()
        if app_ids
        else []
    )
    interviews_done = len(interviews)

    interview_ids = [iv.interview_id for iv in interviews]
    questions = (
        InterviewQuestion.query.filter(
            InterviewQuestion.interview_id.in_(interview_ids)
        ).all()
        if interview_ids
        else []
    )
    q_ids = [q.question_id for q in questions]
    answers = (
        InterviewAnswer.query.filter(InterviewAnswer.question_id.in_(q_ids)).all()
        if q_ids
        else []
    )
    total_answers = len(answers)
    correct_answers = sum(1 for a in answers if a.is_active)
    interview_accuracy = (
        (correct_answers / total_answers * 100) if total_answers else 0
    )

    trend_labels = [a.created_at.strftime("%b %d") for a in apps]
    trend_data = [a.ats_score for a in apps]

    recent = sorted(apps, key=lambda a: a.created_at, reverse=True)[:5]
    recent_rows = []
    for a in recent:
        jd = a.JobDescription
        recent_rows.append(
            {
                "role": jd.job_title if jd else "—",
                "company": jd.company_name if jd else "—",
                "date": a.created_at.strftime("%b %d, %Y"),
                "ats": round(a.ats_score, 1),
            }
        )

    return render_template(
        "user_dashboard.html",
        user=user,
        avg_readiness=round(avg_readiness, 1),
        latest_ats=round(latest_ats, 1),
        interviews_done=interviews_done,
        certifications=certifications,
        interview_accuracy=round(interview_accuracy, 1),
        trend_labels=trend_labels,
        trend_data=trend_data,
        recent_rows=recent_rows,
    )


@app.route("/upload_resume", methods=["post"])
def upload_resume():
    if request.method == "POST":
        resume = request.files["resume"]
        filename = secure_filename(resume.filename)
        # filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        filepath = os.path.join('/tmp',filename)
        desc = request.form["job_description"]
        session["desc"] = desc
        resume.save(filepath)
        content = get_resume_content(filepath)
        if content == 'Error!':
            return redirect(url_for(""))
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
    if "user_id" not in session:
        return redirect(url_for("login"))
    # user dict
    user_id = session["user_id"]
    resume = Resume.query.filter_by(user_id=user_id).first()
    if not resume:
        return redirect(url_for("home"))
    content = resume.resume_text
    desc = session["desc"]
    details = get_job_details(desc)
    if not details.get("title"):
        return redirect(url_for("home"))
    job_desc = JobDescription(
        job_title=details["title"], company_name=details.get("company", ""), job_desc=desc
    )
    db.session.add(job_desc)
    db.session.flush()
    json_content = get_achievements(content)
    session["content"] = json_content
    analysis_quote = get_str_output(content)
    readiness_score = get_readiness_score(content)
    performance = 0
    # Slow since inference calls have high latency
    # ats = get_ats_score(content, session['desc'])
    # Latency Improvement
    ats = get_ats_score(content, desc)["match_score"]
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
        if json_content["platform_links"]:
            performance = get_performance_score(json_content=json_content)
        # Update certifications_count on the instance directly (not via .query.update on an instance)
        job_application.certifications_count = n_crtf
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
    if "user_id" not in session:
        return redirect(url_for("login"))
    ques = get_interview_ques(session["desc"])
    user_id = session["user_id"]
    jobapplication = JobApplication.query.filter_by(user_id=user_id).first()
    interview = MockInterview(application_id=jobapplication.application_id)
    session["application_id"] = jobapplication.application_id
    db.session.add(interview)
    db.session.commit()
    n_ques = len(ques.questions)
    return render_template(
        "mock.html",
        current_ques=0,
        n_ques=n_ques,
        question=ques.questions[0],
        ques_obj=ques,
    )


@app.route("/api/mock-interview/submit", methods=["post"])
def submit():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400
    if "question" not in request.form:
        return jsonify({"error": "No question provided."}), 400

    if "application_id" not in session:
        return jsonify({"error": "Session expired. Please restart the interview."}), 401

    application_id = session["application_id"]
    interview = MockInterview.query.filter_by(application_id=application_id).first()
    if not interview:
        return jsonify({"error": "Invalid interview session. Please restart the interview."}), 401

    audio = request.files["audio"]
    ques = request.form["question"].strip()

    try:
        ans = get_transcription(audio)
    except Exception:
        app.logger.exception("Transcription failed")
        return jsonify({"error": "Transcription failed. Please try again."}), 502

    try:
        is_right = is_answer(ques, ans)
    except Exception:
        app.logger.exception("Answer evaluation failed")
        return jsonify({"error": "Answer evaluation failed. Please try again."}), 502

    question = InterviewQuestion(
        interview_id=interview.interview_id, question_text=ques
    )
    db.session.add(question)
    db.session.flush()
    answer = InterviewAnswer(
        question_id=question.question_id, transcription=ans, is_active=is_right
    )
    db.session.add(answer)
    db.session.commit()
    session["interview_id"] = interview.interview_id
    return jsonify({"is_answer": is_right, "message": "Your Answer is Submitted"})


@app.route("/results")
def results():
    if "interview_id" not in session:
        return redirect(url_for("home"))
    id = session["interview_id"]
    questions = (
        InterviewQuestion.query.filter_by(interview_id=id)
        .options(selectinload(InterviewQuestion.answers))
        .all()
    )

    return render_template("results.html", questions=questions)


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


# Handler for 404 Not Found errors
@app.errorhandler(404)
def page_not_found(error):
    # Pass the status code as a second return value
    return render_template("404.html"), 404


# Handler for 500 Internal Server Errors
@app.errorhandler(500)
def internal_server_error(error):
    # In a real app, you might also want to log the original exception
    # e.original_exception
    return render_template("500.html"), 500


# @app.errorhandler(Exception)
# def handle_general_exception(e):
#     # Default to 500 if the exception doesn't have a specific HTTP code
#     code = getattr(e, 'code', 500)
#     return render_template('error.html', error_code=code, message=str(e)), code


if __name__ == "__main__":
    app.run()
