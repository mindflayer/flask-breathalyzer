from flask import Flask, g
import pytest
import datadog

from flask_breathalyzer import Breathalyzer


@pytest.fixture
def app():
    return Flask(__name__)


def test_initapp(app):
    @app.route("/")
    def boom():
        1/0

    Breathalyzer(app)

    try:
        app.test_client().get('/')
    except Exception as e:
        assert type(e) == datadog.api.exceptions.ApiNotInitialized

    Breathalyzer(app, api_key='api_key', app_key='app_key')

    try:
        app.test_client().get('/')
    except Exception as e:
        assert type(e) == ValueError
        assert 'Invalid JSON response' in e.args[0]
        assert 'Invalid API Key' in e.args[0]

    # from http://docs.datadoghq.com/api/
    options = {
        'api_key': '9775a026f1ca7d1c6c5af9d94d9595a4',
        'app_key': '87ce4a24b5553d2e482ea8a8500e71b8ad4554ff'
    }

    with app.app_context():
        ba = Breathalyzer(app, **options)
        response = app.test_client().get('/')
        assert response.status == '500 INTERNAL SERVER ERROR'
        assert b'<title>500 Internal Server Error</title>' in response.data
        assert response.mimetype == 'text/html'
        assert ba.last_event_id == g.breathalyzer_last_event['event']['id']
