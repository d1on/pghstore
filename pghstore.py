# Copyright (C) 2011 by Hong Minhee <http://dahlia.kr/>,
#                       StyleShare <https://stylesha.re/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
""":mod:`pghstore` --- PostgreSQL hstore formatter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This small module implements a formatter and a loader for hstore_,
one of PostgreSQL_ supplied modules, that stores a simple key-value pairs.

You can easily install the package from PyPI_ by using :program:`pip` or
:program:`easy_install`:

.. sourcecode:: console

   $ pip install pghstore

.. _hstore: http://www.postgresql.org/docs/9.1/static/hstore.html
.. _PostgreSQL: http://www.postgresql.org/
.. _PyPI: http://pypi.python.org/pypi/pghstore

"""
import re
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


__all__ = 'dumps', 'dump'
__version__ = '0.9.0'


def dumps(obj, key_map=None, value_map=None, encoding='utf-8',
          return_unicode=False):
    r"""Converts a mapping object as PostgreSQL ``hstore`` format.

        >>> dumps({u'a': u'1'})
        '"a"=>"1"'
        >>> dumps([('key', 'value'), ('k', 'v')])
        '"key"=>"value","k"=>"v"'

    It accepts only strings as keys and values.  Otherwise it will raise
    :exc:`TypeError`:

        >>> dumps([('a', 1), ('b', 2)])
        Traceback (most recent call last):
          ...
        TypeError: value 1 of key 'a' is not a string

    Or you can pass ``key_map`` and ``value_map`` parameters to workaround
    this:

        >>> dumps([('a', 1), ('b', 2)], value_map=str)
        '"a"=>"1","b"=>"2"'

    By applying these options, you can store any other Python objects
    than strings into ``hstore`` values:

        >>> try:
        ...    import json
        ... except ImportError:
        ...    import simplejson as json
        >>> dumps([('a', range(3)), ('b', 2)], value_map=json.dumps)
        '"a"=>"[0, 1, 2]","b"=>"2"'
        >>> import pickle
        >>> dumps([('a', range(3)), ('b', 2)],
        ...       value_map=pickle.dumps)  # doctest: +ELLIPSIS
        '"a"=>"...","b"=>"..."'

    It returns a UTF-8 encoded string, but you can change the ``encoding``:

        >>> dumps({'surname': u'\ud64d'})
        '"surname"=>"\xed\x99\x8d"'
        >>> dumps({'surname': u'\ud64d'}, encoding='utf-32')
        '"surname"=>"\xff\xfe\x00\x00M\xd6\x00\x00"'

    If you set ``return_unicode`` to ``True``, it will return :class:`unicode`
    instead of :class:`str` (byte string):

        >>> dumps({'surname': u'\ud64d'}, return_unicode=True)
        u'"surname"=>"\ud64d"'

    :param obj: a mapping object to dump
    :param key_map: an optional mapping function that takes a non-string key
                    and returns a mapped string key
    :param value_map: an optional mapping function that takes a non-string
                      value and returns a mapped string value
    :param encoding: a string encode to use
    :param return_unicode: returns an :class:`unicode` string instead
                           byte :class:`str`.  ``False`` by default
    :type return_unicode: :class:`bool`
    :returns: a ``hstore`` data
    :rtype: :class:`basestring`

    """
    b = StringIO.StringIO()
    dump(obj, b, key_map=key_map, value_map=value_map, encoding=encoding)
    result = b.getvalue()
    if return_unicode:
        return result.decode(encoding)
    return result


def dump(obj, file, key_map=None, value_map=None, encoding='utf-8'):
    """Similar to :func:`dumps()` except it writes the result into the passed
    ``file`` object.

        >>> import StringIO
        >>> f = StringIO.StringIO()
        >>> dump({u'a': u'1'}, f)
        >>> f.getvalue()
        '"a"=>"1"'

    :param obj: a mapping object to dump
    :param file: a file object to write into
    :param key_map: an optional mapping function that takes a non-string key
                    and returns a mapped string key
    :param value_map: an optional mapping function that takes a non-string
                      value and returns a mapped string value
    :param encoding: a string encode to use

    """
    if callable(getattr(obj, 'iteritems', None)):
        items = obj.iteritems()
    elif callable(getattr(obj, 'items', None)):
        items = obj.items()
    elif callable(getattr(obj, '__iter__', None)):
        items = iter(obj)
    else:
        raise TypeError('expected a mapping object, not ' + type(obj).__name__)
    if key_map is None:
        def key_map(key):
            raise TypeError('key %r is not a string' % key)
    elif not callable(key_map):
        raise TypeError('key_map must be callable')
    elif not (value_map is None or callable(value_map)):
        raise TypeError('value_map must be callable')
    write = getattr(file, 'write', None)
    if not callable(write):
        raise TypeError('file must be a wrtiable file object that implements '
                        'write() method')
    escape_re = re.compile(r'[\\"]')
    first = True
    for key, value in items:
        if not isinstance(key, basestring):
            key = key_map(key)
        elif not isinstance(key, str):
            key = key.encode(encoding)
        if not isinstance(value, basestring):
            if value_map is None:
                raise TypeError('value %r of key %r is not a string' %
                                (value, key))
            value = value_map(value)
        elif not isinstance(value, str):
            value = value.encode(encoding)
        if first:
            write('"')
            first = False
        else:
            write(',"')
        write(escape_re.sub(r'\\\1', key))
        write('"=>"')
        write(escape_re.sub(r'\\\1', value))
        write('"')
