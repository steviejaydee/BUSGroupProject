import pytest
import json
import os
from unittest.mock import patch, MagicMock
from app.routes import is_online, sync_pending_forms, QUEUE_FILE


def test_offline_queueing(client):
    with client.session_transaction() as sess:
        sess['first_name'] = 'Stevie'
        sess['email'] = 'sxd1008@student.bham.ac.uk'
        sess['lastchecked'] = '2026-04-07T15:40:00'
    with patch('app.routes.is_online', return_value=False):
        response = client.post('/triage', data={
            "name": "Student Offline Test",
            "dob": "1995-01-01",
            "problem": "Testing offline buffer",
            "type": "counselling",
            "addon": "None"
        }, follow_redirects=True)
        assert os.path.exists(QUEUE_FILE)
        with open(QUEUE_FILE, 'r') as f:
            data = json.load(f)
            assert data[-1]['name'] == "Student Offline Test"
        assert b"stable connection" in response.data

def test_online_sync_after_login(client):
    sample_data = [{"name": "Stored Student", "problem": "queued", "type": "none", "addon": ""}]
    with open(QUEUE_FILE, 'w') as f:
        json.dump(sample_data, f)
    with patch('app.routes.is_online', return_value=True):
        with patch('app.routes.send_triage_email', return_value=True) as mock_mail:
            client.post('/login', data={"email": "axb3759@bham.ac.uk", "password": "password123"})
            mock_mail.assert_called_once()
            with open(QUEUE_FILE, 'r') as f:
                assert len(json.load(f)) == 0

def test_online_immediate_send(client):
    with client.session_transaction() as sess:
        sess['email'] = 'axb3759@bham.ac.uk'
        sess['first_name'] = 'Alice'
        sess['lastchecked'] = '2026-04-07T15:40:00'
    with patch('app.routes.is_online', return_value=True):
        with patch('app.routes.send_triage_email', return_value=True) as mock_mail:
            response = client.post('/triage', data={
                "name": "Student Online Test",
                "dob": "1995-01-01",
                "problem": "Testing instant send",
                "type": "cbt",
                "addon": "None"
            }, follow_redirects=True)
            mock_mail.assert_called_once()
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, 'r') as f:
                    data = json.load(f)
                    assert not any(item['name'] == "Student Online Test" for item in data)
            assert b"submitted succesfully" in response.data