"""Auth flow tests: login POST, signup validation, logout, session handling.

Uses an in-memory-safe SQLite file override so tests never touch the real DB.
"""

import os
from datetime import timedelta

import pytest  # noqa: E402

from utils.app import app, db  # noqa: E402
from utils.models import User  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

import main  # noqa: E402,F401  (registers routes)


def _create_user(email, password="password123", name="Test User"):
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_get_login_renders_page(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Welcome Back" in resp.data


def test_login_success_sets_session_and_redirects(client):
    user = _create_user("login.success@example.com", password="password123")
    resp = client.post(
        "/login",
        data={"email": user.email, "password": "password123"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/user_dashboard"
    with client.session_transaction() as sess:
        assert sess["user_id"] == user.id
        assert sess.permanent is True  # permanent cookie per session-hardening decision


def test_login_wrong_password_flashes_and_rerenders(client):
    user = _create_user("login.wrongpass@example.com", password="password123")
    resp = client.post(
        "/login",
        data={"email": user.email, "password": "wrong-password"},
    )
    assert resp.status_code == 200
    # generic flashed message rendered inside login.html (not a plain-text return)
    assert b"Invalid email or password" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_unknown_email_flashes_and_rerenders(client):
    resp = client.post(
        "/login",
        data={"email": "ghost@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_missing_fields_flash(client):
    resp = client.post("/login", data={"email": "", "password": ""})
    assert resp.status_code == 200
    assert b"Email and password are required." in resp.data


def test_signup_rejects_empty_fields(client):
    resp = client.post(
        "/signup",
        data={"username": "", "email": "a@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"All fields are required." in resp.data
    with app.app_context():
        assert User.query.filter_by(email="a@example.com").first() is None


def test_signup_rejects_short_password(client):
    resp = client.post(
        "/signup",
        data={"username": "bob", "email": "shortpw@example.com", "password": "short"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Password must be at least 8 characters long." in resp.data
    with app.app_context():
        assert User.query.filter_by(email="shortpw@example.com").first() is None


def test_signup_rejects_duplicate_email(client):
    existing = _create_user("dup@example.com")
    resp = client.post(
        "/signup",
        data={"username": "dup2", "email": existing.email, "password": "password123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Email already exists" in resp.data
    with app.app_context():
        assert User.query.filter_by(email="dup@example.com").count() == 1


def test_signup_success_hashes_password_and_redirects_to_login(client):
    resp = client.post(
        "/signup",
        data={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    with app.app_context():
        user = User.query.filter_by(email="newbie@example.com").first()
        assert user is not None
        assert user.password_hash != "password123"  # hashed, not plaintext


def test_login_clears_stale_session_keys(client):
    user = _create_user("stale@example.com", password="password123")
    with client.session_transaction() as sess:
        sess["desc"] = "leftover from a previous user"
    resp = client.post(
        "/login",
        data={"email": user.email, "password": "password123"},
    )
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert "desc" not in sess
        assert sess["user_id"] == user.id


def test_login_email_case_insensitive(client):
    _create_user("mixed@example.com", password="password123")
    resp = client.post(
        "/login",
        data={"email": "MIXED@Example.com", "password": "password123"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/user_dashboard"


def test_signup_persists_email_lowercased(client):
    client.post(
        "/signup",
        data={"username": "lower", "email": "UPPER@Example.COM", "password": "password123"},
    )
    with app.app_context():
        assert User.query.filter_by(email="upper@example.com").first() is not None


def test_logout_clears_session_and_redirects_to_login(client):
    user = _create_user("logout@example.com", password="password123")
    client.post(
        "/login",
        data={"email": user.email, "password": "password123"},
    )
    with client.session_transaction() as sess:
        assert "user_id" in sess
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_session_cookie_hardening_configured():
    assert app.secret_key is not None
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(days=7)
