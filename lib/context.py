from .sym import S
from .walkers import TypedTreeWalk, collection_rules

class Context(S):
    def __init__(self, context):
        # TODO: not sure what the literal & context should actually be here
        self._literal = context
        self._context = self
        self._value = ContextValue(context)

class ContextValue:
    '''Context provides two main advantages over using a dict for context:
        - Any unbound symbols are automatically bound to the context, making
          it much easier to write Trace programs
        - Intervention is supported via function-call syntax'''
    def __init__(self, context, context_to_rebind=None):
        '''Any symbols with (context is context_to_rebind) are rebound to the new
        context; by default, unbound symbols (context is None) are rebound.'''
        
        # TreeWalk to rebind symbols
        def bind_Context(l, walk, data):
            # We don't want to re-bind symbols nested in other blocks
            return l
        def bind_S(s, walk, data):
            tp = type(s)
            if s._context is context_to_rebind:
                return tp.as_sym(s._literal, self)
            return tp.as_sym(walk(s._literal, data), walk(s._context, data))
        
        rules = [(Context, bind_Context),
                 *collection_rules,
                 (S, bind_S),
                 (object, lambda o, walk, data: o)]
        
        self.context = TypedTreeWalk(rules)(context)
    
    def __hash__(self):
        return id(self)
    
    def __getitem__(self, item):
        return self.context[item]
    
    def get_copy(self):
        # Any symbols with self as context are rebound to the new context
        return ContextValue(self.context, self)
    
    def __call__(self, intervention):
        new_context = self.get_copy()
        new_context.context.update(intervention)
        return new_context
    
    def __repr__(self):
        return 'Context(' + self.context.__repr__() + ')'
