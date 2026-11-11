import os
import sys

# Make the repo root importable so tests can `import utils` / `import main`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Env vars that utils.app reads at import time. No .env file is committed,
# so tests provide safe defaults before the app module is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GEMINI_API_KEY", "dummy-test-key")
os.environ.setdefault("GROQ_API_KEY", "dummy-test-key")

TEST_DB_FILE = "/tmp/opencode/test_auth.db"
os.environ.setdefault("URI", f"sqlite:///{TEST_DB_FILE}")

import pytest  # noqa: E402

from utils.app import app, db  # noqa: E402
from utils.models import User  # noqa: E402

app.config["TESTING"] = True


@pytest.fixture()
def client():
    with app.app_context():
        db.create_all()
        db.session.query(User).delete()
        db.session.commit()
    with app.test_client() as c:
        with app.app_context():
            yield c
