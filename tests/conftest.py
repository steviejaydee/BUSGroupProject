import pytest
import os
from app import app as flask_app
from app.routes import QUEUE_FILE


@pytest.fixture
def app():
    # Pre-test state: Disable CSRF so the automated client can post [cite: 118]
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret",
    })

    if os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)

    yield flask_app


    if os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)


@pytest.fixture
def client(app):
    return app.test_client()