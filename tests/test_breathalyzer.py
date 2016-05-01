import json
import pytest
import datadog
from flask import Flask

from flask_breathalyzer import Breathalyzer
from flask_breathalyzer.utils import apply_blacklist


@pytest.fixture
def app():
    return Flask(__name__)


def test_initapp(app):
    @app.route("/", methods=['GET', 'POST'])
    def boom():
        1/0

    test_client = app.test_client()

    Breathalyzer(app)

    try:
        test_client.get('/')
    except Exception as e:
        assert type(e) == datadog.api.exceptions.ApiNotInitialized

    Breathalyzer(app, api_key='api_key', app_key='app_key')

    header = 'Accept'
    html = 'text/html'
    try:
        test_client.post('/', data=json.dumps(dict(h=html)), headers=dict(h=html))
    except Exception as e:
        assert type(e) == ValueError
        assert 'Invalid JSON response' in e.args[0]
        assert 'Invalid API Key' in e.args[0]

    # from http://docs.datadoghq.com/api/
    options = {
        'api_key': '9775a026f1ca7d1c6c5af9d94d9595a4',
        'app_key': '87ce4a24b5553d2e482ea8a8500e71b8ad4554ff'
    }

    to_ban = ('to ban', 'Guido Van Rossum')
    to_find = ('to find', 'Raymond Hettinger')
    data = dict((to_ban, to_find))
    h_blacklist = ['/{0}'.format(header)]
    d_blacklist = ['/{0}'.format(to_ban[0])]
    ba = Breathalyzer(app, headers_blacklist=h_blacklist, data_blacklist=d_blacklist, **options)
    assert ba.last_event_id is None
    response = test_client.post('/', data=data)
    assert response.status == '500 INTERNAL SERVER ERROR'
    assert b'<title>500 Internal Server Error</title>' in response.data
    assert response.mimetype == 'text/html'
    assert 'ZeroDivisionError' in ba.last_event['event']['text']
    assert ba.last_event_id == ba.last_event['event']['id']
    assert to_ban[1] not in ba.last_event['event']['text']
    assert to_find[1] in ba.last_event['event']['text']


def test_apply_blacklist():
    v = 'foobar'
    d1 = dict(a=1, b=dict(c=3, d=dict(e=4)))
    d2 = apply_blacklist(d1, ('/a', '/b/d/e'), value_to_replace=v)
    assert d2 == dict(a=v, b=dict(c=3, d=dict(e=v)))
    assert id(d1) != id(d2)
