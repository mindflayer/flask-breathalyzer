"""
from raven module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    _iteritems = "items"
    MAXSIZE = sys.maxsize
else:
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


def apply_blacklist(dic, lis, separator='/', value_to_replace='BLACKLISTED'):
    """
    :param dic: dictionary with some potential keys to blacklist
    :param lis: list (or tuple) of string paths (via /slashed/paths XPATH style) to blacklist
    :param separator: str separator used to reach the nested values
    :param value_to_replace: value to replace blacklisted ones
    :return: a new dictionary without the blacklisted elements
    """
    class NestedDict(dict):
        """
        Nested dictionary of arbitrary depth with autovivification.
        Allows data access via extended slice notation.
        http://stackoverflow.com/questions/15077973/how-can-i-access-a-deeply-nested-dictionary-using-tuples
        """
        def __getitem__(self, keys):
            # Let's assume *keys* is a list or tuple.
            if isinstance(keys, (tuple, list)):
                try:
                    node = self
                    for key in keys:
                        node = dict.__getitem__(node, key)
                    return node
                except TypeError:
                    # *keys* is not a list or tuple.
                    pass
            try:
                return dict.__getitem__(self, keys)
            except KeyError:
                raise KeyError(keys)

        def __setitem__(self, keys, value):
            # Let's assume *keys* is a list or tuple.
            if isinstance(keys, (tuple, list)):
                try:
                    node = self
                    for key in keys[:-1]:
                        try:
                            node = dict.__getitem__(node, key)
                        except KeyError:
                            node[key] = type(self)()
                            node = node[key]
                    return dict.__setitem__(node, keys[-1], value)
                except TypeError:
                    # *keys* is not a list or tuple.
                    pass
            dict.__setitem__(self, keys, value)
    nd = NestedDict(dic)
    for l in lis:
        keys = l.split(separator)[1:]
        try:
            nd[keys]
        except KeyError:
            pass
        else:
            nd[keys] = value_to_replace
    return nd
