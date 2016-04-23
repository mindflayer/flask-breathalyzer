from __future__ import absolute_import
import traceback
import sys
import json

from flask import request, current_app, g
from flask.signals import got_request_exception, request_finished
from werkzeug.exceptions import ClientDisconnected
try:
    from flask_login import current_user
except ImportError:
    has_flask_login = False
else:
    has_flask_login = True

from flask_breathalyzer.utils import (
    text_type, string_type, integer_types, to_unicode, urlparse, get_headers, get_environ
)

import datadog

# # Use Statsd, a Python client for DogStatsd
# from datadog import statsd
#
# statsd.increment('whatever')
# statsd.gauge('foo', 42)
#
# # Or ThreadStats, an alternative tool to collect and flush metrics, using Datadog REST API
# from datadog import ThreadStats
# stats = ThreadStats()
# stats.start()
# stats.increment('home.page.hits')


class Breathalyzer(object):
    """
        options = {
            'api_key':'api_key',
            'app_key':'app_key'
        }
    """

    def __init__(self, app=None, client=None, register_signal=True, **datadog_options):

        self.client = client
        self.register_signal = register_signal
        self.app = None

        if app:
            self.init_app(app, client, datadog_options, register_signal)

    def init_app(self, app, client, options, register_signal=None):

        datadog.initialize(**options)

        self.app = app

        if client is None:
            self.client = datadog.api

        if register_signal is not None:
            self.register_signal = register_signal

        app.before_request(self.before_request)

        if self.register_signal:
            got_request_exception.connect(self.handle_exception, sender=app)
            request_finished.connect(self.after_request, sender=app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['breathalyzer'] = self

    @property
    def last_event_id(self):
        return g.breathalyzer_last_event['event']['id']

    def before_request(self, *args, **kwargs):
        self.last_event_id = None
        # FIXME from Sentry module
        try:
            self.client.http_context(self.get_http_info())
        except Exception as e:
            self.client.logger.exception(to_unicode(e))
        try:
            self.client.user_context(Breathalyzer.get_user_info())
        except Exception as e:
            self.client.logger.exception(to_unicode(e))

    def after_request(self, sender, response, *args, **kwargs):
        if self.last_event_id:
            response.headers['X-Breathalyzer-ID'] = self.last_event_id
        self.client.context.clear()  # FIXME from Sentry module
        return response

    def is_json_type(self, content_type):
        return content_type == 'application/json'

    def get_form_data(self):
        return request.form

    def get_json_data(self):
        return request.data

    def get_http_info_with_retriever(self, retriever=None):
        """
        Exact method for getting http_info but with form data work around.
        """
        if retriever is None:
            retriever = self.get_form_data

        urlparts = urlparse.urlsplit(request.url)

        try:
            data = retriever()
        except ClientDisconnected:
            data = {}

        return {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': data,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }

    def get_http_info(self):
        """
        Determine how to retrieve actual data by using request.mimetype.
        """
        if self.is_json_type(request.mimetype):
            retriever = self.get_json_data
        else:
            retriever = self.get_form_data
        return self.get_http_info_with_retriever(retriever)

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return

        ignored_exc_type_list = current_app.config.get(
            'BREATHALYZER_IGNORE_EXCEPTIONS', [])
        exc = sys.exc_info()[1]

        if any((isinstance(exc, ignored_exc_type)
                for ignored_exc_type in ignored_exc_type_list)):
            return

        self.capture_exception(exc_info=kwargs.get('exc_info'))

    @staticmethod
    def get_user_info():
        """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/)
        to be installed
        and setup
        """
        if not has_flask_login:
            return

        if not hasattr(current_app, 'login_manager'):
            return

        try:
            is_authenticated = current_user.is_authenticated
        except AttributeError:
            # HACK: catch the attribute error thrown by flask-login is not attached
            # >   current_user = LocalProxy(lambda: _request_ctx_stack.top.user)
            # E   AttributeError: 'RequestContext' object has no attribute 'user'
            return {}

        if callable(is_authenticated):
            is_authenticated = is_authenticated()

        if not is_authenticated:
            return {}

        user_info = {
            'id': current_user.get_id(),
        }

        # if 'SENTRY_USER_ATTRS' in current_app.config:
        #     for attr in current_app.config['SENTRY_USER_ATTRS']:
        #         if hasattr(current_user, attr):
        #             user_info[attr] = getattr(current_user, attr)

        return user_info

    def capture_exception(self, *args, **kwargs):
        # Get a formatted version of the traceback.
        exc = traceback.format_exc()

        # Make request.headers json-serializable.
        szble = {}
        for k, v in request.headers:
            k = k.upper().replace('-', '_')
            if isinstance(v, (list, string_type, bool, float) + integer_types):
                szble[k] = v
            else:
                szble[k] = text_type(v)

        title = 'Exception from {0}'.format(request.path)
        text = "Traceback:\n@@@\n{0}\n@@@\nMetadata:\n@@@\n{1}\n@@@" \
            .format(exc, json.dumps(szble, indent=2))

        # Submit the exception to Datadog
        g.breathalyzer_last_event = self.client.Event.create(
            title=title,
            text=text,
            tags=[self.app.import_name, 'exception'],
            aggregation_key=request.path,
            alert_type='error',
        )

