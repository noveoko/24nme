import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

def test_home_page():
    client = app.app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data
