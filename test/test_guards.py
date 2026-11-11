"""login_required guard tests: each protected route redirects to /login when unauthenticated."""

import pytest  # noqa: E402

from utils.app import app, db  # noqa: E402
from utils.models import User  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

import main  # noqa: E402,F401  (registers routes)


@pytest.fixture()
def client():
    with app.app_context():
        db.create_all()
        db.session.query(User).delete()
        db.session.commit()
    with app.test_client() as c:
        with app.app_context():
            yield c


@pytest.mark.parametrize(
    "path",
    [
        "/user_dashboard",
        "/dashboard",
        "/mock",
        "/results",
        "/dashboard/certificates",
    ],
)
def test_protected_route_redirects_to_login_when_unauthenticated(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
