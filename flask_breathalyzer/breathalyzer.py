from __future__ import absolute_import

from flask import request, current_app, g
try:
    from flask_login import current_user
except ImportError:
    has_flask_login = False
else:
    has_flask_login = True

from flask_breathalyzer.utils import to_unicode

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

    def __init__(self, app=None, client=None, **datadog_options):

        self.client = client

        if app:
            self.init_app(app, client, datadog_options)

    @property
    def last_event_id(self):
        return getattr(self, '_last_event_id', None)

    def init_app(self, app, client, options):

        datadog.initialize(**options)

        if client is None:
            self.client = datadog.api

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['breathalyzer'] = self

    @last_event_id.setter
    def last_event_id(self, value):
        self._last_event_id = value
        try:
            g.sentry_event_id = value  # FIXME from Sentry module
        except Exception:
            pass

    def before_request(self, *args, **kwargs):
        self.last_event_id = None
        # FIXME from Sentry module
        try:
            self.client.http_context(self.get_http_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))
        try:
            self.client.user_context(self.get_user_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))

    def after_request(self, sender, response, *args, **kwargs):
        if self.last_event_id:
            response.headers['X-Breathalyzer-ID'] = self.last_event_id
        self.client.context.clear()  # FIXME from Sentry module
        return response

    def get_user_info(self, request):
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