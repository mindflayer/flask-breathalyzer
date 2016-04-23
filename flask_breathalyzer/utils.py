"""
from raven module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys
import types

PY2 = sys.version_info[0] == 2

if not PY2:
    string_type = str,
    integer_types = (int,),
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_type = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

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

if not PY2:
    _iterkeys = "keys"
    _itervalues = "values"
    _iteritems = "items"
    _iterlists = "lists"
else:
    _iterkeys = "iterkeys"
    _itervalues = "itervalues"
    _iteritems = "iteritems"
    _iterlists = "iterlists"

try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse  # NOQA

urlparse = _urlparse


def iteritems(d, **kw):
    """Return an iterator over the (key, value) pairs of a dictionary."""
    return iter(getattr(d, _iteritems)(**kw))


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.
    Objects of protected types are preserved as-is when passed to
    force_text(strings_only=True).
    """
    import Decimal
    import datetime
    return isinstance(obj, integer_types + (type(None), float, Decimal,
        datetime.datetime, datetime.date, datetime.time))


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_text, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first, saves 30-40% when s is an instance of
    # text_type. This function gets called often in that setting.
    if isinstance(s, text_type):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if not isinstance(s, string_type):
            if hasattr(s, '__unicode__'):
                s = s.__unicode__()
            else:
                if not PY2:
                    if isinstance(s, bytes):
                        s = text_type(s, encoding, errors)
                    else:
                        s = text_type(s)
                else:
                    s = text_type(bytes(s), encoding, errors)
        else:
            # Note: We use .decode() here, instead of text_type(s, encoding,
            # errors), so that if s is a SafeBytes, it ends up being a
            # SafeText at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            raise UnicodeDecodeError(*e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_text(arg, encoding, strings_only, errors) for arg in s])
    return s


def to_unicode(value):
    try:
        value = text_type(force_text(value))
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = '(Error decoding value)'
    except Exception:  # in some cases we get a different exception
        try:
            value = binary_type(repr(type(value)))
        except Exception:
            value = '(Error decoding value)'
    return value


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
