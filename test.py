from lib.sym import S, E
from lib.context import Context

import sys
import operator as op

import unittest

def tern(cond, tval, fval):
    return tval if cond else fval

class TestTrace(unittest.TestCase):
    def test_symbol(self):
        self.assertEqual(S('x', {'x': 2}).get_value(), 2)
        self.assertEqual(S(1, {1: 'a'}).get_value(), 'a')
    
    def test_nested_symbol(self):
        self.assertEqual(S('x', S('context', {'context': {'x': 2}})).get_value(), 2)
    
    def test_symbolic_literal(self):
        self.assertEqual(S(S('x', {'x': 2}), {2:4}), 4)

    def test_eval(self):
        self.assertEqual(E(op.add, [2, 3]).get_value(), 5)
    
    def test_factorial_dynamic_structure(self):
        fact = Context({
            'fact_code': Context({
                'recursive_call': E(tern, [S('n') == 1,
                                           Context({'res': 1}),
                                           S('fact')]),
                'res': S('n') * S('res', S('recursive_call')({'n': S('n') - 1}))
            }),
            'fact': S('fact_code')({'fact': S('fact')}),
            'res': S('res', S('fact')({'n': S('n')}))
        })
        
        self.assertEqual(fact({'n': 4})['res'].get_value(), 24)
        self.assertEqual(S('res', fact({'n': 4})).get_value(), 24)
    
    def test_factorial_symbolic_literal(self):
        fact = Context({
            'fact_code': Context({
                'res': S(S('n') == 0, {
                    True: 1,
                    False: S('n')*S('res', S('fact')({'n': S('n') - 1}))
                })
            }),
            'fact': S('fact_code')({'fact': S('fact')}),
            'res': S('res', S('fact')({'n': S('n')}))
        })
        
        self.assertEqual(fact({'n': 4})['res'].get_value(), 24)
    
    def test_factorial_call_context(self):
        fact = Context({
            'fact': Context({
                'res': S(S('n') == 0, {
                    True: 1,
                    False: S('n')*S('res', S('fact')({'n': S('n') - 1}))
                })
            })({'fact': S('fact')}),
            'res': S('res', S('fact')({'n': S('n')}))
        })
        
        self.assertEqual(fact({'n': 4})['res'].get_value(), 24)
    
    def test_bad_factorial(self):
        recursion_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(200)
        
        # Since we have to get the value of both legs before calling the ternary op, this infinite loops
        bad_fact = Context({
            'fact_code': Context({
                'res': E(tern, [S('n') == 0, 1, S('n')*S('res', S('fact')({'n': S('n') - 1}))])
            }),
            'fact': S('fact_code')({'fact': S('fact')}),
            'res': S('res', S('fact')({'n': S('n')}))
        })
        
        caught = None
        try:
            bad_fact({'n': 3})['res'].get_value()
        except Exception as e:
            caught = e
        self.assertEqual(type(caught), RecursionError)
        sys.setrecursionlimit(recursion_limit)
    
    def test_dynamic_context(self):
        dynamic = Context({
           'base': Context({}),
           'intervention': {'n': 2, 'res': S('n', S('construct'))*3},
           'construct': S('base')(S('intervention')),
           'res': S('res', S('construct'))
        })
        
        self.assertEqual(dynamic['res'].get_value(), 6)
        
if __name__ == '__main__':
    unittest.main()
