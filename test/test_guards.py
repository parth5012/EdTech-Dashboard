"""login_required guard tests: each protected route redirects to /login when unauthenticated."""

import pytest  # noqa: E402

import main  # noqa: E402,F401  (registers routes; client fixture comes from conftest.py)


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
