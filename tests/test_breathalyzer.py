import json
import os
import pytest
import datadog
from flask import Flask
import flask.ext.login as flask_login

from flask_breathalyzer import Breathalyzer
from flask_breathalyzer.utils import apply_blacklist


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def test_client_instance(app):
    return app.test_client()


@pytest.fixture
def test_client(app):
    return app.test_client


@pytest.fixture
def path_info():
    return '/boom'


@pytest.fixture
def secret_key():
    return os.urandom(24)


@pytest.fixture
def user_id():
    return 'DrunkUser'


def test_failing_initapp(app, test_client_instance, path_info):
    @app.route(path_info)
    def boom():
        1 / 0

    Breathalyzer(app)

    try:
        test_client_instance.get(path_info)
    except Exception as e:
        assert type(e) == datadog.api.exceptions.ApiNotInitialized

    Breathalyzer(app, api_key='api_key', app_key='app_key')

    try:
        test_client_instance.get(path_info)
    except Exception as e:
        assert type(e) == ValueError
        assert 'Invalid JSON response' in e.args[0]
        assert 'Invalid API Key' in e.args[0]


def test_succesful_event(app, test_client, path_info, secret_key, user_id):
    @app.route(path_info, methods=['GET', 'POST'])
    def boom():
        1 / 0

    # from http://docs.datadoghq.com/api/
    options = {
        'api_key': '0c82710457ebeaeab1c901c0152852fa',
        'app_key': 'b8e5af1010d49ac73cadde2a5be5ef01b6ae73c6'
    }

    header = 'Accept'
    html = 'text/html'
    headers = {header: html}
    to_ban = ('to ban', 'Guido Van Rossum')
    to_find = ('to find', 'Raymond Hettinger')
    data = dict((to_ban, to_find))
    h_blacklist = ['/{0}'.format(header)]
    d_blacklist = ['/{0}'.format(to_ban[0])]

    app.secret_key = secret_key
    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def user_loader(username):
        class User(flask_login.UserMixin):
            def get_id(self):
                return user_id
        return User()

    login_manager.init_app(app)

    ba = Breathalyzer(app, headers_blacklist=h_blacklist, data_blacklist=d_blacklist, **options)
    assert ba.last_event_id is None

    with test_client() as c:
        with c.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['_fresh'] = True
        response = c.post(path_info, data=json.dumps(data), content_type='application/json', headers=headers)

    assert response.status == '500 INTERNAL SERVER ERROR'
    assert b'<title>500 Internal Server Error</title>' in response.data
    assert response.mimetype == 'text/html'
    assert 'ZeroDivisionError' in ba.last_event['event']['text']
    assert ba.last_event_id == ba.last_event['event']['id']
    assert to_ban[1] not in ba.last_event['event']['text']
    assert to_find[1] in ba.last_event['event']['text']
    assert user_id in ba.last_event['event']['text']


def test_apply_blacklist():
    v = 'foobar'
    d1 = dict(a=1, b=dict(c=3, d=dict(e=4)))
    d2 = apply_blacklist(d1, ('/a', '/b/d/e', '/z'), value_to_replace=v)
    assert d2 == dict(a=v, b=dict(c=3, d=dict(e=v)))
    assert id(d1) != id(d2)
