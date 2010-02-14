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

The read-only versions arent very well protected. They are only there as
reminders to the honest programmer who makes mistakes.

I have also stuck with the dict-like naming convention of all lowercase names
with no word seperators.

Internally the mapping is represented as a list of (key, value) pairs (which
is what maintains the order) AND a mapping of keys to a list of positions in
the pair list (for making everything faster).

"""


import collections
from bisect import bisect

class MultiMap(collections.Mapping):
    """An ordered mapping which supports multiple values for the same key."""
    
    def __init__(self, *args, **kwargs):
        """Initialize a MultiMap.
        
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
        
        """
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
        self._rebuild_key_ids()
    
    def _rebuild_key_ids(self):
        """Rebuild the internal key to index mapping."""
        self._key_ids = collections.defaultdict(list)
        for i, x in enumerate(self._pairs):
            self._key_ids[x[0]].append(i)
    
    def _conform_key(self, key):
        """Force a given key into certain form.
        
        For overiding.
        
        """
        return key
    
    def _conform_value(self, value):
        """Force a given value into certain form.

        For overiding.

        """
        return value
    
    def _conform_pair(self, pair):
        """Force a given key/value pair into a certain form.
        
        Override the _conform_key and _conform_value if you want to change
        the mapping behaviour.
        
        """
        pair = tuple(pair)
        if len(pair) != 2:
            raise ValueError('MultiMap element must have length 2')
        return (self._conform_key(pair[0]), self._conform_value(pair[1]))
        
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._pairs)
    
    def __nonzero__(self):
        """
        
        >>> bool(MultiMap([]))
        False
        >>> bool(MultiMap(a=1))
        True
        
        """
        return len(self._pairs)
    
    def __getitem__(self, key):
        """Get the FIRST value for this key.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m['a']
        1
        >>> m['b']
        2
        >>> m['x']
        Traceback (most recent call last):
        ...
        KeyError: 'x'
            
        """
        key = self._conform_key(key)
        try:
            return self._pairs[self._key_ids[key][0]][1]
        except IndexError:
            raise KeyError(key)
    
    def __contains__(self, key):
        """Is a key in this mapping?
        
        >>> m = MultiMap(a=1)
        >>> 'a' in m
        True
        >>> 'x' in m
        False
        
        """
        return self._conform_key(key) in self._key_ids
    
    def __len__(self):
        """The number of different keys.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> len(m)
        4
        
        """
        return len(self._key_ids)
    
    def alllen(self):
        """The number of pairs. Includes duplicate keys.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.alllen()
        6
        
        """
        return len(self._pairs)
    
    def getall(self, key):
        """A list of all the values stored under this key.
        
        Returns an empty list if there are no values under this key.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.getall('a')
        [1]
        >>> m.getall('b')
        [2, 3]
        >>> m.getall('x')
        []
        
        """
        key = self._conform_key(key)
        return [self._pairs[i][1] for i in self._key_ids[key]]
    
    def iteritems(self):
        """Iterator across all the unique keys and their values.
        
        Only yields the first key of duplicated.
        
        """
        keys_yielded = set()
        for k, v in self._pairs:
            if k not in keys_yielded:
                keys_yielded.add(k)
                yield k, v
                
    def __iter__(self):
        """Iterate across the unique keys in the mapping."""
        return (x[0] for x in self.iteritems())
    
    def keys(self):
        """A list of the first keys in the mapping, in order.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.keys()
        ['a', 'b', 'c', 'd']
        
        """
        return list(self)
    
    def iterkeys(self):
        """Iterate across the first keys in the mapping."""
        return iter(self)
    
    def iterallkeys(self):
        """Iterate across ALL of the keys in the mapping, in order."""
        for x in self._pairs:
            yield x[0]
    
    def allkeys(self):
        """A list of ALL of the keys in the mapping, in order.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.allkeys()
        ['a', 'b', 'b', 'c', 'd', 'c']
        
        """
        return [x[0] for x in self._pairs]
    
    def items(self):
        """A list of items with the first keys in the mapping.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.items()
        [('a', 1), ('b', 2), ('c', 4), ('d', 5)]
        
        """
        return list(self.iteritems())
    
    def itervalues(self):
        """Iterate across the value for the first keys in the mapping."""
        return (x[1] for x in self.iteritems())
    
    def values(self):
        """A list of values for the first keys in the mapping.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.values()
        [1, 2, 4, 5]
        
        """
        return list(self.itervalues())
    
    def iterallvalues(self):
        """Iterate across ALL of the values in the mapping."""
        for x in self._pairs:
            return x[1]
    
    def allvalues(self):
        """A list of ALL values in the mapping.
        
        >>> m = MultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m.allvalues()
        [1, 2, 3, 4, 5, 6]
        
        """
        return [x[1] for x in self._pairs]
    
    def iterallitems(self):
        """Iterate across ALL of the pairs in the mapping."""
        return iter(self._pairs)
    
    def allitems(self):
        """A list of ALL of the pairs in the mapping."""
        return self._pairs[:]


class MutableMultiMap(MultiMap, collections.MutableMapping):
    """An ordered mapping which supports multiple values for the same key.

    >> m = MutableMultiMap({'a': 1, 'b': 2})
    >> m
    MutableMultiMap([('a', 1), ('b', 2)])

    >> m = MutableMultiMap([('a', 1), ('b', 2)])
    >> m
    MutableMultiMap([('a', 1), ('b', 2)])

    >> m = MutableMultiMap(a=1, b=2)
    >> m
    MutableMultiMap([('a', 1), ('b', 2)])


    >> m['a']
    1

    >> m['c'] = 3
    >> m['c']
    3

    >> m.setlist('c', [1, 2, 3])
    >> m['c']
    1
    >> m.getall('c')
    [1, 2, 3]

    >> m.keys()
    ['a', 'b', 'c']
    >> m.allkeys()
    ['a', 'b', 'c', 'c', 'c']
    >> m.allvalues()
    [1, 2, 1, 2, 3]
    >> len(m)
    3
    >> m.alllen()
    5

    >> m['c'] = 4
    >> m.getall('c')
    [4]

    >> m.append((1, 2))
    >> m.allitems()
    [('a', 1), ('b', 2), ('c', 4), (1, 2)]

    >> m.popitem()
    (1, 2)

    >> m.popitem(0)
    ('a', 1)
    
    >> M = MutableMultiMap([('a', 0), ('b', 1), ('c', 2), ('b', 3), ('c', 4), ('c', 5)])
    
    >> m = M.copy()
    >> m.pop('b')
    1
    >> m
    MutableMultiMap([('a', 0), ('c', 2), ('c', 4), ('c', 5)])
    
    >> m = M.copy()
    >> m.popone('b')
    1
    >> m
    MutableMultiMap([('a', 0), ('c', 2), ('b', 3), ('c', 4), ('c', 5)])
    
    >> m.popall('c')
    [2, 4, 5]
    >> m
    MutableMultiMap([('a', 0), ('b', 3)])
    
    >> m = M.copy()
    >> m.popitem()
    ('c', 5)
    >> m.popitem(0)
    ('a', 0)
    
    """
    
    def __delitem__(self, key):
        """Remove all key/value pairs by the given key.
        
        Raises a KeyError if there are none.
        
        >>> m = MutableMultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> del m['a']
        >>> m
        MutableMultiMap([('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> m['b']
        2
        >>> m.getall('c')
        [4, 6]
        
        >>> m = MutableMultiMap([('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5), ('c', 6)])
        >>> del m['b']
        >>> m
        MutableMultiMap([('a', 1), ('c', 4), ('d', 5), ('c', 6)])
        >>> m['a']
        1
        >>> m['c']
        4
        >>> m.getall('c')
        [4, 6]
        
        >>> m = MutableMultiMap(a=1)
        >>> del m['x']
        Traceback (most recent call last):
        ...
        KeyError: 'x'
        
        """
        key = self._conform_key(key)
        del_ids = self._key_ids[key]
        if not del_ids:
            raise KeyError(key)
        
        # Remove the ids.
        del self._key_ids[key]
        
        self._remove_pairs(del_ids)
    
    def _remove_pairs(self, ids_to_remove):
        """Remove the pairs identified by the given indices into _pairs.
        
        Removes the pair, and updates the _key_ids mapping to be accurate.
        Removing the ids from the _key_ids is your own responsibility.
        
        Params:
            ids_to_remove -- The indices to remove. MUST be sorted.
        
        """
        # Remove them.
        for i in reversed(ids_to_remove):
            del self._pairs[i]
        
        # We use the bisect to tell us how many spots the given index is
        # shifting up in the list.
        for ids in self._key_ids.itervalues():
            for i, id in enumerate(ids):
                ids[i] -= bisect(ids_to_remove, id)
    
    def _update_for_new_ids(self, insert_ids):
        """Update the _key_ids mapping for adding some new pairs.
        
        This must be called BEFORE the new items are added to _key_ids map.
        
        Params:
            insert_ids -- Where the new items will be inserted.
        
        """
        # We use the bisect to tell us how many spots the given index is
        # shifting up in the list.
        for ids in self._key_ids.itervalues():
            for i, id in enumerate(ids):
                ids[i] += bisect(insert_ids, id)
    
    def discard(self, key):
        """Same as del m[key], but does not throw an error."""
        try:
            del self[key]
        except KeyError:
            pass

    def __setitem__(self, key, value):
        key = self._conform_key(key)
        if isinstance(value, (tuple, list)):
            self.setlist(key, value)
        else:
            self.remove(key)
            self._pairs.append((key, self._conform_value(value)))

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
    >> def gen():
    ...     print 'generating'
    ...     for x in range(5):
    ...         yield (x, 'x')
    >> m = DelayedMultiMap(gen)
    >> m[0]
    generating
    'x'
    >> m[5] = 'new'
    Traceback (most recent call last):
    ...
    TypeError: 'DelayedMultiMap' object does not support item assignment

    """
    
    pass

class DelayedMutableMultiMap(DelayedTraits, MutableMultiMap):
    """
    >> def gen():
    ...     print 'generating'
    ...     for x in range(5):
    ...         yield (x, 'x')
    >> m = DelayedMutableMultiMap(gen)
    >> m[0]
    generating
    'x'
    >> m[5] = 'new'
    >> m
    DelayedMutableMultiMap([(0, 'x'), (1, 'x'), (2, 'x'), (3, 'x'), (4, 'x'), (5, 'new')])
    
    """
    
    pass


# def test_conform_methods():
#     class CaseInsensitive(MutableMultiMap):
#         def _conform_key(self, key):
#             return key.lower()
#     d = CaseInsensitive()
#     d['a'] = 1
#     d['A'] = 2
#     assert len(d) == 1
#     assert d['a'] == 2
#     d['Content-Encoding'] = 'deflate'
#     assert 'content-encoding' in d
#     assert 'blah' not in d

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
