import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

def test_home_page():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'https://cdn.jsdelivr.net/npm/bootstrap@' in response.data