from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from utils.llms import get_resume_content, get_json_output, get_str_output, get_readiness_score
from utils.stats import get_performance_score
app = Flask(__name__)


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create it if it doesn’t exist

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

resume_path = 0


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload_resume', methods=['post'])
def upload_resume():
    if request.method == 'POST':
        resume = request.files['resume']
        filename = secure_filename(resume.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(filepath)
        global resume_path
        resume_path = filepath

    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    content = get_resume_content(resume_path)
    json_content = get_json_output(content)
    analysis_quote = get_str_output(content)
    readiness_score = get_readiness_score(content)
    performance = 0
    if json_content:
        if json_content['platform link']:
            performance = get_performance_score(json_content=json_content)
        n_crtf = len(json_content['certifications'])
    else:
        performance= None
    return render_template('dashboard.html', quote=analysis_quote, readiness_score=readiness_score, n_crtf=n_crtf, performance=performance)


if __name__ == "__main__":
    app.run()
