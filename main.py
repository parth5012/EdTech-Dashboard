from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from utils.llms import (
    get_resume_content,
    get_json_output,
    get_str_output,
    get_readiness_score,
    is_answer,
    get_interview_ques,
    get_ats_score,
)
from utils.stats import get_performance_score
from utils.verification import verify_public_badge
from utils.answer import get_transcription

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create it if it doesn’t exist

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

resume_path = 0


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload_resume", methods=["post"])
def upload_resume():
    if request.method == "POST":
        resume = request.files["resume"]
        filename = secure_filename(resume.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        desc = request.form["job_description"]
        session["desc"] = desc
        resume.save(filepath)
        global resume_path
        resume_path = filepath
        # session["desc"] = desc

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "desc" not in session:
        return redirect(url_for("home"))
    content = get_resume_content(resume_path)
    json_content = get_json_output(content)
    session["content"] = json_content
    analysis_quote = get_str_output(content)
    readiness_score = get_readiness_score(content)
    performance = 0
    # ats = get_ats_score(content, desc)
    ats = 25
    if json_content:
        if json_content["platform link"]:
            performance = get_performance_score(json_content=json_content)
        n_crtf = len(json_content["certifications"])
    else:
        performance = None
    return render_template(
        "dashboard.html",
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
    if content["certificate links"]:
        list = content["certificate links"]
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
    return render_template("mock.html",)


@app.route("/results")
def results():
    return render_template("results.html")


if __name__ == "__main__":
    app.run(debug=True)
