import operator as op

class BaseSymbol:
    def __getitem__(self, item):
        return S(item, self)
        #return E(op.getitem, GreedyList([self, item]))
    
    def __call__(self, args):
        def call(x, y):
            return x(y)
        return E(call, GreedyList([self, args]))
    
    def __lt__(self, other):
        return E(op.lt, GreedyList([self, other]))
    
    def __le__(self, other):
        return E(op.le, GreedyList([self, other]))
    
    def __eq__(self, other):
        return E(op.eq, GreedyList([self, other]))
    
    def __ne__(self, other):
        return E(op.ne, GreedyList([self, other]))
    
    def __gt__(self, other):
        return E(op.gt, GreedyList([self, other]))
    
    def __ge__(self, other):
        return E(op.ge, GreedyList([self, other]))
    
    def __add__(self, other):
        return E(op.add, GreedyList([self, other]))
    
    def __sub__(self, other):
        return E(op.sub, GreedyList([self, other]))
    
    def __mul__(self, other):
        return E(op.mul, GreedyList([self, other]))
    
    def __matmul__(self, other):
        return E(op.matmul, GreedyList([self, other]))
    
    def __truediv__(self, other):
        return E(op.truediv, GreedyList([self, other]))
    
    def __floordiv__(self, other):
        return E(op.floordiv, GreedyList([self, other]))
    
    def __mod__(self, other):
        return E(op.mod, GreedyList([self, other]))
    
    def __divmod__(self, other):
        return E(op.divmod, GreedyList([self, other]))
    
    def __pow__(self, other):
        return E(op.pow, GreedyList([self, other]))
    
    def __lshift__(self, other):
        return E(op.lshift, GreedyList([self, other]))
    
    def __rshift__(self, other):
        return E(op.rshift, GreedyList([self, other]))
    
    def __and__(self, other):
        return E(op.and_, GreedyList([self, other]))
    
    def __xor__(self, other):
        return E(op.xor, GreedyList([self, other]))
    
    def __or__(self, other):
        return E(op.or_, GreedyList([self, other]))
    
    def __radd__(self, other):
        return E(op.add, GreedyList([other, self]))
    
    def __rsub__(self, other):
        return E(op.sub, GreedyList([other, self]))
    
    def __rmul__(self, other):
        return E(op.mul, GreedyList([other, self]))
    
    def __rmatmul__(self, other):
        return E(op.matmul, GreedyList([other, self]))
    
    def __rtruediv__(self, other):
        return E(op.truediv, GreedyList([other, self]))
    
    def __rfloordiv__(self, other):
        return E(op.floordiv, GreedyList([other, self]))
    
    def __rmod__(self, other):
        return E(op.mod, GreedyList([other, self]))
    
    def __rlshift__(self, other):
        return E(op.lshift, GreedyList([other, self]))
    
    def __rrshift__(self, other):
        return E(op.rshift, GreedyList([other, self]))
    
    def __rand__(self, other):
        return E(op.and_, GreedyList([other, self]))
    
    def __rxor__(self, other):
        return E(op.xor, GreedyList([other, self]))
    
    def __ror__(self, other):
        return E(op.or_, GreedyList([other, self]))
    
    # TODO: unary numeric operators

class Uncomputed:
    pass
uncomputed = Uncomputed()

def maybe_resolve(s):
    if isinstance(s, S):
        #print(s._literal, s._context)
        return s.get_value()
    return s

class S(BaseSymbol):
    # Symbol class
    def __init__(self, literal, context=None):
        self._literal = literal
        self._context = context
        self._value = uncomputed
    
    @staticmethod
    def as_sym(literal, context):
        # Used by subclasses with different call patterns, to construct as though they were S
        # TODO: get rid of this and just standardize constructors instead?
        return S(literal, context)
    
    def get_value(self):
        if self._value is uncomputed:
            self._value = self.resolve()
        return self._value
    
    def resolve(self):
        expr = maybe_resolve(self._context)[maybe_resolve(self._literal)]
        return maybe_resolve(expr)
    
    def __repr__(self):
        return 'S(' + self._literal.__repr__() + ')'

class E(S):
    # TODO: handle both args and kwargs
    def __init__(self, f, args):
        self._literal = args
        self._context = f
        self._value = uncomputed
    
    @staticmethod
    def as_sym(literal, context):
        return E(context, literal)
    
    def resolve(self):
        args = [maybe_resolve(a) for a in maybe_resolve(self._literal)]
        return self._context(*args)
    
    def unpack(self):
        return {'context': self._context, 'literal': self._literal}
    
    @staticmethod
    def pack(context, literal):
        return E(context, literal)

    def __repr__(self):
        return 'E(' + str(self._literal) +')'

# TODO: use these to make sure symbols in collections are resolved before being passed to python functions
# TODO: move walk() method inside of Symbol subclasses so that extension is possible without changing walker?
#   - Counterargument: probably already possible via E with appropriate constructors, though not necessarily pretty
def arg_list(*args):
    return args

class GreedyList(E):
    # This is a non-lazy list type, It has two main use-cases:
    # - output lists, where you don't want a list of unresolved symbols
    # - inputs for python functions which operate on lists (e.g. map() of a python func)
    def __init__(self, l):
        self._literal = l
        self._context = arg_list
        self._value = uncomputed
    
    def resolve(self):
        return [maybe_resolve(item) for item in maybe_resolve(self._literal)]
    
    def __getitem__(self, ind):
        return maybe_resolve(self._literal)[ind]
    
    def __iter__(self):
        return maybe_resolve(self._literal).__iter__()
    
    def __len__(self):
        return maybe_resolve(self._literal).__len__()

class LazyList(E):
    def __init__(self, l):
        self._literal = l
        self._context = arg_list  # Not *quite* accurate...
        self._value = uncomputed
    
    def resolve(self):
        return LazyListValue(maybe_resolve(self._literal))
    
    def __getitem__(self, ind):
        return self._literal[ind]
    
    def __iter__(self):
        return self._literal.__iter__()
    
    def __len__(self):
        return self._literal.__len__()

class LazyListValue(list):
    def __getitem__(self, item):
        return maybe_resolve(super().__getitem__(item))
    
    def __iter__(self):
        for item in super().__iter__():
            yield maybe_resolve(item)
        return
    
    def __call__(self, intervention):
        new_l = [item for item in self]
        for k, v in intervention.items():
            new_l[k] = v
        return LazyListValue(new_l)

def kwarg_dict(**kwargs):
    return kwargs

class Dict(E):
    # NOTE: this one doesn't work yet
    def __init__(self, d):
        self._literal = kwarg_dict
        self._context = d  # TODO: make E handle kwargs
        self._value = uncomputed
    
    def resolve(self):
        return {k: maybe_resolve(v) for k, v in self._context.items()}
