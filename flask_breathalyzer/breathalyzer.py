from __future__ import absolute_import
import traceback
import json

import datadog
from flask import request
from flask import _app_ctx_stack as app_context
from flask.signals import got_request_exception, request_finished
from werkzeug.exceptions import ClientDisconnected
try:
    from flask_login import current_user
except ImportError:
    has_flask_login = False
else:
    has_flask_login = True

from flask_breathalyzer.utils import (
    urlparse, get_headers, get_environ, apply_blacklist
)


class Breathalyzer(object):
    """
        options = {
            'api_key':'api_key',
            'app_key':'app_key'
        }
    """

    def __init__(
            self, app=None, client=None, register_signal=True,
            data_blacklist=None, headers_blacklist=None, **datadog_options
    ):

        self.client = client
        self.register_signal = register_signal
        self.app = None
        self.data_blacklist = data_blacklist
        self.headers_blacklist = headers_blacklist

        if app:
            self.init_app(app, datadog_options)

    def init_app(self, app, options):

        self.app = app

        if self.client is None:
            datadog.initialize(**options)
            self.client = datadog.api

        if self.register_signal and self.client:
            got_request_exception.connect(self.handle_exception, self.app)
            request_finished.connect(self.after_request, self.app)

        if not hasattr(self.app, 'extensions'):
            self.app.extensions = {}
        self.app.extensions['breathalyzer'] = self

    @property
    def last_event_id(self):
        try:
            return self.last_event['event']['id']
        except TypeError:
            return None

    @property
    def last_event(self):
        last_event = getattr(app_context, 'breathalyzer_last_event', None)
        if last_event is not None:
            return last_event

    def after_request(self, sender, response, **extra):
        if self.last_event_id:
            response.headers['X-Breathalyzer-ID'] = self.last_event_id
        return response

    @staticmethod
    def get_form_data():
        return request.form

    @staticmethod
    def get_json_data():
        return request.get_json(force=True)

    def get_http_info_with_retriever(self, retriever=None):
        """
        Exact method for getting http_info but with form data work around.
        """
        if retriever is None:
            retriever = self.get_form_data

        url_parts = urlparse.urlsplit(request.url)

        try:
            data = retriever()
        except ClientDisconnected:
            data = {}

        headers = dict(get_headers(request.environ))

        if self.data_blacklist:
            data = apply_blacklist(data, self.data_blacklist)
        if self.headers_blacklist:
            headers = apply_blacklist(headers, self.headers_blacklist)

        return {
            'url': '%s://%s%s' % (url_parts.scheme, url_parts.netloc, url_parts.path),
            'query_string': url_parts.query,
            'method': request.method,
            'data': data,
            'headers': headers,
            'env': dict(get_environ(request.environ)),
        }

    def get_http_info(self):
        """
        Determine how to retrieve actual data, basically if it's JSON or not.
        """
        try:
            is_json = request.is_json
        except AttributeError:
            is_json = request.get_json(silent=True) is not None
        if is_json:
            retriever = Breathalyzer.get_json_data
        else:
            retriever = Breathalyzer.get_form_data
        return self.get_http_info_with_retriever(retriever)

    def handle_exception(self, sender, exception, **extra):
        if not self.client:
            return

        ignored_exc_type_list = sender.config.get(
            'BREATHALYZER_IGNORE_EXCEPTIONS', [])

        if any((isinstance(exception, ignored_exc_type) for ignored_exc_type in ignored_exc_type_list)):
            return

        self.capture_exception()

    def get_user_info(self):
        """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/)
        to be installed
        and setup
        """
        if not has_flask_login:
            return

        if not hasattr(self.app, 'login_manager'):
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

        return dict(id=current_user.get_id())

    def capture_exception(self):
        # Get a formatted version of the traceback.
        exc = traceback.format_exc()

        info = dict(http_info=self.get_http_info(), user_info=self.get_user_info())

        title = 'Exception from {0}'.format(request.path)
        text = "Traceback:\n@@@\n{0}\n@@@\nMetadata:\n@@@\n{1}\n@@@" \
            .format(exc, json.dumps(info, indent=2))

        # Submit the exception to Datadog
        app_context.breathalyzer_last_event = self.client.Event.create(
            title=title,
            text=text,
            tags=[self.app.import_name, 'exception'],
            aggregation_key=request.path,
            alert_type='error',
        )
