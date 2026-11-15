import uuid
from flask import session, get_flashed_messages
from utils.models import User, MockInterview, InterviewQuestion, InterviewAnswer
from utils.app import app, db
import main  # noqa: E402, F401


def test_results_without_interview_id_redirects_and_flashes(client):
    user_id = uuid.uuid4()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    resp = client.get("/results", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"

    # Check flashed messages
    with client.session_transaction() as sess:
        # Flask stores _flashes in session: list of (category, message)
        flashes = sess.get("_flashes", [])
        assert ("error", "Please complete an interview first") in flashes


def test_results_without_interview_id_redirect_renders_flash_on_home(client):
    user_id = uuid.uuid4()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    resp = client.get("/results", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please complete an interview first" in resp.data


def test_results_template_renders_no_answer_recorded(client):
    with app.app_context():
        class DummyQuestion:
            question_text = "What is Python?"
            answers = []

        from flask import render_template

        rendered = render_template("results.html", questions=[DummyQuestion()])
        assert "What is Python?" in rendered
        assert "No answer recorded" in rendered
        assert "Incorrect" in rendered


def test_results_template_renders_existing_answer(client):
    with app.app_context():
        class DummyAnswer:
            transcription = "Python is a programming language"
            is_active = True

        class DummyQuestion:
            question_text = "What is Python?"
            answers = [DummyAnswer()]

        from flask import render_template

        rendered = render_template("results.html", questions=[DummyQuestion()])
        assert "What is Python?" in rendered
        assert "Python is a programming language" in rendered
        assert "Correct" in rendered
