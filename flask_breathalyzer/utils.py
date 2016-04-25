"""
from raven module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    binary_type = bytes
    _iteritems = "items"
    MAXSIZE = sys.maxsize

else:
    binary_type = str
    _iteritems = "iteritems"

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):
            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
            del X

try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse  # NOQA

urlparse = _urlparse


def iteritems(d, **kw):
    """Return an iterator over the (key, value) pairs of a dictionary."""
    return iter(getattr(d, _iteritems)(**kw))


# `get_headers` comes from `werkzeug.datastructures.EnvironHeaders`
def get_headers(environ):
    """
    Returns only proper HTTP headers.
    """
    for key, value in iteritems(environ):
        key = str(key)
        if key.startswith('HTTP_') and key not in \
           ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
            yield key[5:].replace('_', '-').title(), value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            yield key.replace('_', '-').title(), value


def get_environ(environ):
    """
    Returns our whitelisted environment variables.
    """
    for key in ('REMOTE_ADDR', 'SERVER_NAME', 'SERVER_PORT'):
        if key in environ:
            yield key, environ[key]
