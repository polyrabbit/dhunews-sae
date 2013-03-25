class Nothing(object):
    """return Nothing to avoid the use of if(check if returned is None)"""
    def __new__(cls, *args, **kwargs):
    	if '_inst' not in vars(cls):
            cls._inst = super(Nothing, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self
    def __repr__(self): return 'Nothing()'
    def __str__(self): return 'Nothing'
    def __nonzero__(self): return False
    def __getattr__(self, name): return self
    def __setattr__(self, name, value): return self
    def __delattr__(self, name): return self
    def __len__(self): return 0
    def __iter__(self): return iter(())
    def __getitem__(self, k): return self
    def __setitem__(self, k, v): return self
    def __delitem__(self, k): return self