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


"""

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

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
    
    >>> m.pop()
    (1, 2)
    
    >>> m.pop(0)
    ('a', 1)
    
    """
    
    def __init__(self, *args, **kwargs):
        self._pairs = []
        for arg in args:
            if isinstance(arg, collections.Mapping):
                self.update(arg)
            else:
                self.extend(arg)
        self.update(kwargs)
    
    def _conform_key(self, key):
        return key
    
    def _conform_value(self, value):
        return value
    
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
    
    def __delitem__(self, key):
        key = self._conform_key(key)
        self._pairs = [x for x in self._pairs if x[0] != key]
    
    def __setitem__(self, key, value):
        key = self._conform_key(key)
        if isinstance(value, (tuple, list)):
            self.setlist(key, value)
        else:
            del self[key]
            self._pairs.append((self._conform_key(key), self._conform_value(value)))
    
    def setlist(self, key, value):
        key = self._conform_key(key)
        del self[key]
        for v in value:
            self._pairs.append((key, self._conform_value(v)))
    
    def sort(self, *args, **kwargs):
        self._pairs.sort(*args, **kwargs)
    
    def _conform_pair(self, pair):
        pair = tuple(pair)
        if len(pair) != 2:
            raise ValueError('pair must be length 2')
        return (self._conform_key(pair[0]), self._conform_value(pair[1]))
            
    def append(self, pair):
        self._pairs.append(self._conform_pair(pair))
    
    def extend(self, pairs):
        self._pairs.extend(self._conform_pair(x) for x in pairs)
    
    def pop(self, *args):
        return self._pairs.pop(*args)
    
    def insert(self, index, pair):
        self._pairs.insert(index, self._conform_pair(pair))
    
    def update(self, mapping):
        for k, v in mapping.items():
            del self[k]
            self[k] = v
    
    def copy(self):
        return self.__class__(self._pairs[:])
    

if __name__ == '__main__':
    from . import test
    test.run()