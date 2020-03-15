from .sym import S, E

class TreeWalk:
    def __init__(self, rules):
        self.rules = rules
    
    def __call__(self, expr, data=None):
        for is_match, replace in self.rules:
            if not is_match(expr):
                continue
            return replace(expr, self, data)
        return expr

class TypedTreeWalk(TreeWalk):
    # Walk a nested data structure, with operation at each node determined by its type
    def __init__(self, rules):
        def get_type_checker(t):
            return lambda obj: isinstance(obj, t)
        self.rules = [(get_type_checker(t), op) for t, op in rules]

# pack & unpack are used to pretend that every collection is a dict,
# so we can just code for dict and then re-use that for everything else
unpack = {
    #E: lambda e: e.unpack(),
    dict: lambda d: d,
    list: lambda l: {i: l[i] for i in range(len(l))},
    #Dict: lambda d: d._value,
    #List: lambda l: {i: l._value[i] for i in range(len(l._value))}
}

pack = {
    #E: lambda e: E.pack(**e),
    dict: lambda d: d,  # Always wrap dicts and lists, if they're not wrapped already
    list: lambda l: [l[i] for i in range(len(l))],
    #Dict: lambda d: Dict(d),
    #List: lambda l: List([l[i] for i in range(len(l))])
}

def get_bind_collection(tp):
    def bind_collection(coll, walk, data):
        '''Walk all elements of collection; mainly used for rebinding symbols within collections'''
        d = unpack[tp](coll)
        result = {k: walk(d[k], data) for k in d}
        return pack[tp](result)
    return bind_collection
# Most TreeWalks use the same collection rules
collection_rules = [(tp, get_bind_collection(tp)) for tp in unpack]
