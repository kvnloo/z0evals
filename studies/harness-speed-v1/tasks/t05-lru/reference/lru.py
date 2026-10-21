from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        if capacity < 1: raise ValueError(capacity)
        self.cap = capacity; self.d = OrderedDict()
    def get(self, k):
        if k not in self.d: return -1
        self.d.move_to_end(k); return self.d[k]
    def put(self, k, v):
        self.d[k] = v; self.d.move_to_end(k)
        if len(self.d) > self.cap: self.d.popitem(last=False)
    def __len__(self): return len(self.d)
