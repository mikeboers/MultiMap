# coding: UTF-8
u"""Module for a URI query parser.

It has dictionary like access. While this class will accept more than one
value per key (a key can be repeated) the dictionary methods will tend to
return only the first of those values. Care has been taken, however, to always
maintain the order of the multiple values.

NOTE that I do NOT treat '+' as a space! It will stay a '+'. Spaces MUST be
percent encoded to be picked up.

TODO: make sure that is what jquery does.

Instantiate with a string:

    >>> query = Query('key1=value1&key2=value2')
    >>> query.items()
    [(u'key1', u'value1'), (u'key2', u'value2')]

Instantiate with a dict:

    >>> query = Query({u'a': 1, u'b': 2})
    >>> sorted(query.allitems())
    [(u'a', u'1'), (u'b', u'2')]

Instantiate with a list of pairs:

    >>> query = Query([('one', u'1'), ('two', u'2')])
    >>> query.allitems()
    [(u'one', u'1'), (u'two', u'2')]

Cast back to a string:
    >>> str(query)
    'one=1&two=2'

It can deal with multiple values per key (although by all the normal dict methods it does not appear this way).:

    >>> query = Query('key=value1&key=value2')
    >>> query['key']
    u'value1'

    >>> query.list('key')
    [u'value1', u'value2']

    >>> query.allitems()
    [(u'key', u'value1'), (u'key', u'value2')]

Order is maintained very precisely, even with multiple values per key:

    >>> query = Query('a=1&b=2&a=3')
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'a', u'3')]

Setting is a little more difficult. Assume that unless something that extends a tuple or list (ie passes isinstance(input, (tuple, list))) it is supposed to be the ONLY string value for that key.

    >>> # Notice that we are still using the query with multiple values for a.
    >>> query.list(u'a')
    [u'1', u'3']
    >>> query[u'a'] = 'value'
    >>> query.list(u'a')
    [u'value']

Setting a list:

    >>> query['key'] = 'a b c'.split()
    >>> query.list('key')
    [u'a', u'b', u'c']

You can provide a sequence that is not a tuple or list by using the setlist method. This will remove all existing pairs by key, and append the new ones on the end of the query.

    >>> def g():
    ... 	for x in [1, 2, 3]:
    ... 		yield x
    >>> query.setlist('key', g())
    >>> query.list('key')
    [u'1', u'2', u'3']

The query can be sorted via list.sort (notice that the key function is passed a key/value tuple):

    >>> query = Query('a=1&c=2&b=3')
    >>> query.sort()
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'3'), (u'c', u'2')]
    >>> query.sort(key=lambda x: -ord(x[0]))
    >>> query.allitems()
    [(u'c', u'2'), (u'b', u'3'), (u'a', u'1')]

Pairs can be appended with list.append and list.insert and list.extend. (We will just cast the values to tuples and assert they have length 2.)

    >>> query = Query()
    >>> query.append((u'a', u'1'))
    >>> query.allitems()
    [(u'a', u'1')]

    >>> query.extend(sorted({u'b': 2, u'c': 3}.items()))
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'c', u'3')]

    >>> query.insert(0, ('z', '-1'))
    >>> query.allitems()
    [(u'z', u'-1'), (u'a', u'1'), (u'b', u'2'), (u'c', u'3')]

You can update the query via dict.update:

    >>> query = Query()
    >>> query.update({u'a': 1, u'b': [2, 3], u'c': u'4'})
    >>> query.sort() # Because the dictionary does not come in order.
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'b', u'3'), (u'c', u'4')]

    >>> query.update({u'b': '2/3'})
    >>> query.sort() # Dicts are not ordered!
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2/3'), (u'c', u'4')]

Empty queries test as false:
    >>> bool(Query())
    False
    >>> bool(Query('a=b'))
    True

Empty queries are empty:
    >>> query = Query('')
    >>> query
    <uri.Query:[]>
    >>> print query
    <BLANKLINE>

Parse and unparses properly
    
    >>> parse('key=value')
    [(u'key', u'value')]
    >>> parse('key=')
    [(u'key', u'')]
    >>> parse('key')
    [(u'key', None)]
    
    >>> query = Query('key')
    >>> query['a'] = None
    >>> query
    <uri.Query:[(u'key', None), (u'a', None)]>
    >>> str(query)
    'key&a'
    
    >>> query = Query('key=value/with/slashes.and.dots=and=equals')
    >>> query
    <uri.Query:[(u'key', u'value/with/slashes.and.dots=and=equals')]>
    >>> str(query)
    'key=value/with/slashes.and.dots=and=equals'

Unicode does work properly.
    >>> query = Query('k%C3%A9y=%C2%A1%E2%84%A2%C2%A3%C2%A2%E2%88%9E%C2%A7%C2%B6%E2%80%A2%C2%AA%C2%BA')
    >>> print query.keys()[0]
    kéy
    >>> print query[u'kéy']
    ¡™£¢∞§¶•ªº
    
    >>> query = Query()
    >>> query[u'kéy'] = u'¡™£¢∞§¶•ªº'
    >>> print query
    k%C3%A9y=%C2%A1%E2%84%A2%C2%A3%C2%A2%E2%88%9E%C2%A7%C2%B6%E2%80%A2%C2%AA%C2%BA
    
Easy signatures!

# >>> query = Query('v=value')
# >>> # query.add_nonce(u'n', length=8)
# >>> query[u'n'] = '12345'
# >>> query.sign_with_md5(hmac_key='this is the key', sig_key=u's')
# >>> str(query)
# [(u'v', 'value'), (u'n', '12345'), (u's', 'md5signgoesinhere')]
# 
# >>> query.sign('this is the key')
# True
# >>> query.verify_signature('this is not the key')
# False

"""

def unicoder(obj, encoding='UTF-8', errors='replace'):
    if isinstance(obj, unicode):
        return obj
    return unicode(str(obj), encoding, errors)

import collections
from transcode import *

def parse(query):
    ret = []
    if not query:
        return ret
    for pair in query.split(u'&'):
        pair = [decode(x) for x in pair.split(u'=', 1)]
        if isinstance(pair[0], str):
            pair = [unicoder(x) for x in pair]
        if len(pair) == 1:
            pair.append(None)
        ret.append(tuple(pair))
    return ret

def unparse(pairs):
    ret = []
    for pair in pairs:
        if pair[1] is None:
            ret.append(encode(pair[0], u'/'))
        else:
            ret.append(encode(pair[0], u'/') + u'=' + encode(pair[1], '/='))
    return u'&'.join(ret)

class Query(object):
    
    def __init__(self, input=None):
        self._pairs = []
        if isinstance(input, basestring):
            self._pairs = parse(input)
        elif isinstance(input, collections.Mapping):
            self.update(input)
        elif input is not None:
            self.extend(input)
    
    def __str__(self):
        return unparse(self._pairs)
    
    def __repr__(self):
        return '<uri.Query:%r>' % self._pairs
    
    def __nonzero__(self):
        return len(self._pairs)
    
    def __getitem__(self, key):
        key = unicoder(key)
        for x in self._pairs:
            if x[0] == key:
                return x[1]
    
    def list(self, key):
        key = unicoder(key)
        return [x[1] for x in self._pairs if x[0] == key]
    
    def iteritems(self):
        keys_yielded = set()
        for k, v in self._pairs:
            if k not in keys_yielded:
                keys_yielded.add(k)
                yield k, v
                
    def __iter__(self):
        return (x[0] for x in self.iteritems())
    
    def keys(self):
        return list(self)
    
    def iterkeys(self):
        return iter(self)
    
    def items(self):
        return list(self.iteritems())
    
    def itervalues(self):
        return (x[1] for x in self.iteritems())
    
    def values(self):
        return list(self.itervalues())
    
    def iterallitems(self):
        return iter(self._pairs)
    
    def allitems(self):
        return self._pairs[:]
    
    def __delitem__(self, key):
        key = unicoder(key)
        self._pairs = [x for x in self._pairs if x[0] != key]
    
    def __setitem__(self, key, value):
        key = unicoder(key)
        if isinstance(value, (tuple, list)):
            self.setlist(key, value)
        else:
            del self[key]
            self._pairs.append((unicoder(key), self._conform_value(value)))
    
    def setlist(self, key, value):
        key = unicoder(key)
        del self[key]
        for v in value:
            self._pairs.append((key, self._conform_value(v)))
    
    def sort(self, *args, **kwargs):
        self._pairs.sort(*args, **kwargs)
    
    def _conform_pair(self, pair):
        pair = tuple(pair)
        if len(pair) != 2:
            raise ValueError('Pair must be length 2.')
        return (unicoder(pair[0]), self._conform_value(pair[1]))
    
    def _conform_value(self, value):
        if value is None:
            return None
        return unicoder(value)
            
    def append(self, pair):
        self._pairs.append(self._conform_pair(pair))
    
    def extend(self, pairs):
        self._pairs.extend(self._conform_pair(x) for x in pairs)
    
    def insert(self, index, pair):
        self._pairs.insert(index, self._conform_pair(pair))
    
    def update(self, mapping):
        for k, v in mapping.iteritems():
            del self[k]
            self[k] = v

if __name__ == '__main__':
    import doctest
    print 'Testing', __file__
    doctest.testmod()
    print 'Done.'