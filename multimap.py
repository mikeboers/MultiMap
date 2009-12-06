"""Module for various mapping which allow multiple values per key. As a by
product of how they are controlled they also maintain order.

The API of these objects tends towards being a drop-in replacement for normal
mappings. All the dict methods will return only the first occourance of a key.
Even len(map) will return the number of unique keys, not the number of pairs
stored. Many dict methods have an "all" prefixed version which does the same
thing but to all key-value pairs. Thusly, multiple of the same key may be
returned while using them.

Several list methods are also exposed, such as insert, extend, pop, etc.
Primary testing can be found in the nitrogen.uri.query module.

Unfortunately the read-only versions arent very well protected. I guess they
are only there as reminders to the honest programmer who makes mistakes.

I have also stuck with the dict-like naming convention of all lowercase names
with no word seperators. Oh well.

"""


import collections

class MultiMap(collections.Mapping):
    """An ordered mapping which supports multiple values for the same key.
    
    >>> m = MultiMap({'a': 1, 'b': 2})
    >>> m
    MultiMap([('a', 1), ('b', 2)])
    
    >>> m = MultiMap([('a', 1), ('b', 2)])
    >>> m
    MultiMap([('a', 1), ('b', 2)])
    
    >>> m = MultiMap(a=1, b=2)
    >>> m
    MultiMap([('a', 1), ('b', 2)])
    
    >>> m = MultiMap([('a', 1), ('b', 2), ('c', 3), ('c', 4)])
    >>> m
    MultiMap([('a', 1), ('b', 2), ('c', 3), ('c', 4)])
    
    
    >>> m['a']
    1
    
    >>> m.getall('c')
    [3, 4]
    
    >>> m.keys()
    ['a', 'b', 'c']
    >>> m.allkeys()
    ['a', 'b', 'c', 'c']
    >>> m.allvalues()
    [1, 2, 3, 4]
    >>> len(m)
    3
    >>> m.alllen()
    4
    
    >>> m['d'] = 5
    Traceback (most recent call last):
    ...
    TypeError: 'MultiMap' object does not support item assignment
    
    """
    
    def __init__(self, *args, **kwargs):
        self._pairs = []
        for arg in args:
            if isinstance(arg, collections.Mapping):
                for x in arg.items():
                    self._pairs.append(self._conform_pair(x))
            else:
                for x in arg:
                    self._pairs.append(self._conform_pair(x))
        for x in kwargs.items():
            self._pairs.append(self._conform_pair(x))
    
    def _conform_key(self, key):
        return key
    
    def _conform_value(self, value):
        return value
    
    def _conform_pair(self, pair):
        pair = tuple(pair)
        if len(pair) != 2:
            raise ValueError('MultiMap element must have length 2')
        return (self._conform_key(pair[0]), self._conform_value(pair[1]))
        
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._pairs)
    
    def __nonzero__(self):
        return len(self._pairs)
    
    def __getitem__(self, key):
        key = self._conform_key(key)
        for x in self._pairs:
            if x[0] == key:
                return x[1]
        raise KeyError(key)
    
    def __contains__(self, key):
        key = self._conform_key(key)
        return any(x[0] == key for x in self._pairs)
    
    def __len__(self):
        return len(set(x[0] for x in self._pairs))
    
    def alllen(self):
        return len(self._pairs)
    
    def getall(self, key):
        key = self._conform_key(key)
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
    
    def iterallkeys(self):
        for x in self._pairs:
            yield x[0]
    
    def allkeys(self):
        return [x[0] for x in self._pairs]
    
    def items(self):
        return list(self.iteritems())
    
    def itervalues(self):
        return (x[1] for x in self.iteritems())
    
    def values(self):
        return list(self.itervalues())
    
    def iterallvalues(self):
        for x in self._pairs:
            return x[1]
    
    def allvalues(self):
        return [x[1] for x in self._pairs]
    
    def iterallitems(self):
        return iter(self._pairs)
    
    def allitems(self):
        return self._pairs[:]


class MutableMultiMap(MultiMap, collections.MutableMapping):
    """An ordered mapping which supports multiple values for the same key.

    >>> m = MutableMultiMap({'a': 1, 'b': 2})
    >>> m
    MutableMultiMap([('a', 1), ('b', 2)])

    >>> m = MutableMultiMap([('a', 1), ('b', 2)])
    >>> m
    MutableMultiMap([('a', 1), ('b', 2)])

    >>> m = MutableMultiMap(a=1, b=2)
    >>> m
    MutableMultiMap([('a', 1), ('b', 2)])


    >>> m['a']
    1

    >>> m['c'] = 3
    >>> m['c']
    3

    >>> m.setlist('c', [1, 2, 3])
    >>> m['c']
    1
    >>> m.getall('c')
    [1, 2, 3]

    >>> m.keys()
    ['a', 'b', 'c']
    >>> m.allkeys()
    ['a', 'b', 'c', 'c', 'c']
    >>> m.allvalues()
    [1, 2, 1, 2, 3]
    >>> len(m)
    3
    >>> m.alllen()
    5

    >>> m['c'] = 4
    >>> m.getall('c')
    [4]

    >>> m.append((1, 2))
    >>> m.allitems()
    [('a', 1), ('b', 2), ('c', 4), (1, 2)]

    >>> m.popitem()
    (1, 2)

    >>> m.popitem(0)
    ('a', 1)
    
    >>> M = MutableMultiMap([('a', 0), ('b', 1), ('c', 2), ('b', 3), ('c', 4), ('c', 5)])
    
    >>> m = M.copy()
    >>> m.pop('b')
    1
    >>> m
    MutableMultiMap([('a', 0), ('c', 2), ('c', 4), ('c', 5)])
    
    >>> m = M.copy()
    >>> m.popone('b')
    1
    >>> m
    MutableMultiMap([('a', 0), ('c', 2), ('b', 3), ('c', 4), ('c', 5)])
    
    >>> m.popall('c')
    [2, 4, 5]
    >>> m
    MutableMultiMap([('a', 0), ('b', 3)])
    
    >>> m = M.copy()
    >>> m.popitem()
    ('c', 5)
    >>> m.popitem(0)
    ('a', 0)
    
    """
    
    def remove(self, key):
        key = self._conform_key(key)
        self._pairs = [x for x in self._pairs if x[0] != key]
    
    def __delitem__(self, key):
        len_before = len(self._pairs)
        self.remove(key)
        if len(self._pairs) == len_before:
            raise KeyError(key)

    def __setitem__(self, key, value):
        key = self._conform_key(key)
        if isinstance(value, (tuple, list)):
            self.setlist(key, value)
        else:
            self.remove(key)
            self._pairs.append((self._conform_key(key), self._conform_value(value)))

    def setlist(self, key, value):
        key = self._conform_key(key)
        self.remove(key)
        for v in value:
            self._pairs.append((key, self._conform_value(v)))

    def sort(self, *args, **kwargs):
        self._pairs.sort(*args, **kwargs)

    def append(self, pair):
        self._pairs.append(self._conform_pair(pair))

    def extend(self, pairs):
        self._pairs.extend(self._conform_pair(x) for x in pairs)

    def pop(self, key, *args):
        key = self._conform_key(key)
        try:
            ret = self[key]
        except KeyError:
            if args:
                return args[0]
            raise
        self.remove(key)
        return ret
    
    def popall(self, key):
        key = self._conform_key(key)
        ret = self.getall(key)
        self.remove(key)
        return ret
    
    def popone(self, key, *args):
        key = self._conform_key(key)
        try:
            ret = self[key]
        except KeyError:
            if args:
                return args[0]
            raise
        for i in range(len(self._pairs)):
            if self._pairs[i][0] == key:
                self._pairs.pop(i)
                break
        return ret
    
    def popitem(self, *args):
        return self._pairs.pop(*args)

    def insert(self, index, pair):
        self._pairs.insert(index, self._conform_pair(pair))

    def update(self, mapping):
        for k, v in mapping.items():
            self.remove(k)
            self[k] = v

    def copy(self):
        return self.__class__(self._pairs[:])


class DelayedTraits(object):
    def __init__(self, supplier=None):
        self.supplier = supplier
        self._setup = False
        self.__pairs = None

    @property
    def _pairs(self):
        if not self._setup:
            self.__pairs = [(self._conform_key(k), self._conform_value(v)) for
                k, v in self.supplier()]
            self._setup = True
        return self.__pairs
    
    @_pairs.setter
    def _pairs(self, value):
        self.__pairs = value

class DelayedMultiMap(DelayedTraits, MultiMap):
    """
    >>> def gen():
    ...     print 'generating'
    ...     for x in range(5):
    ...         yield (x, 'x')
    >>> m = DelayedMultiMap(gen)
    >>> m[0]
    generating
    'x'
    >>> m[5] = 'new'
    Traceback (most recent call last):
    ...
    TypeError: 'DelayedMultiMap' object does not support item assignment

    """
    
    pass

class DelayedMutableMultiMap(DelayedTraits, MutableMultiMap):
    """
    >>> def gen():
    ...     print 'generating'
    ...     for x in range(5):
    ...         yield (x, 'x')
    >>> m = DelayedMutableMultiMap(gen)
    >>> m[0]
    generating
    'x'
    >>> m[5] = 'new'
    >>> m
    DelayedMutableMultiMap([(0, 'x'), (1, 'x'), (2, 'x'), (3, 'x'), (4, 'x'), (5, 'new')])
    
    """
    
    pass


def test_conform_methods():
    class CaseInsensitive(MutableMultiMap):
        def _conform_key(self, key):
            return key.lower()
    d = CaseInsensitive()
    d['a'] = 1
    d['A'] = 2
    assert len(d) == 1
    assert d['a'] == 2
    d['Content-Encoding'] = 'deflate'
    assert 'content-encoding' in d
    assert 'blah' not in d

if __name__ == '__main__':
    from . import test
    test.run()
