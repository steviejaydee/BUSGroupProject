import sys
import os

# This adds the parent directory to Python's path so it can find 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

import pytest
import json
from unittest.mock import patch, mock_open

# 1. Create a fake Database
# This mimics your users.json structure exactly, but only exists during the test.
MOCK_USERS_DB = [
    {"first_name": "Alice", "email": "axb3759@student.bham.ac.uk", "password": "password123", "role": "student"},
    {"first_name": "admin", "email": "admin@bham.ac.uk", "password": "admin", "role": "admin"}
]
MOCK_JSON_STR = json.dumps(MOCK_USERS_DB)


# Setup the Flask Test Client

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'super_secret_test_key'

    flask_app.config['WTF_CSRF_ENABLED'] = False

    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


# The Tests

# test 1 - logg in
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_JSON_STR)
def test_successful_admin_login(mock_file, client):
    """Admin logs in and is sent straight to the admin dashboard."""

    response = client.post('/login', data={
        'first_name': 'admin',
        'email': 'admin@bham.ac.uk',
        'password': 'admin'
    })

    # to verify the redirect goes to the admin page, not index
    assert response.status_code == 302
    assert response.location == '/admin'

# --- DELETE TESTS ---

# test 2 delete
@patch('json.dump')  # Intercept the save function
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_JSON_STR)
def test_admin_can_delete_user(mock_file, mock_json_dump, client):
    """the admin successfully deletes a user, horray!."""

    # Bypass the login screen and set the session directly to admin
    with client.session_transaction() as session:
        session['first_name'] = 'admin'

    response = client.get('/delete_user/1')

    # Verify it redirected back to the admin dashboard
    assert response.status_code == 302
    assert response.location == '/admin'

    # Verify json.dump was called with the updated database (Alice removed)
    # mock_json_dump.call_args[0][0] captures the first argument passed to json.dump
    saved_data = mock_json_dump.call_args[0][0]

    assert len(saved_data) == 1  # Only 1 user should be left
    assert saved_data[0]['first_name'] == 'admin'  # The admin is the only one left


# test 3
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_JSON_STR)
def test_non_admin_cannot_delete_user(mock_file, client):
    """standard student role tries to access the delete route."""

    with client.session_transaction() as session:
        session['first_name'] = 'Alice'  # Standard user session

    response = client.get('/delete_user/2')

    # Verify the block kicks them back to the index page
    assert response.status_code == 302
    assert response.location == '/'


# --- EDIT TESTS ---

# test 4
@patch('json.dump')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_JSON_STR)
def test_admin_can_edit_user(mock_file, mock_json_dump, client):
    """admin edits a user's role and email."""

    with client.session_transaction() as session:
        session['first_name'] = 'admin'

    # Send a POST request to edit Alice (row_id=1).
    response = client.post('/edit_user/1', data={
        'email': 'new_alice_email@bham.ac.uk',
        'role': 'alumni'
    })

    assert response.status_code == 302
    assert response.location == '/admin'

    # Inspect what the app tried to save to users.json
    saved_data = mock_json_dump.call_args[0][0]

    # Verify the specific fields were updated
    assert saved_data[0]['email'] == 'new_alice_email@bham.ac.uk'
    assert saved_data[0]['role'] == 'alumni'

    # Verify the fields we left blank were NOT overwritten with None
    assert saved_data[0]['first_name'] == 'Alice'