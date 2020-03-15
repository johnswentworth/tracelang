# Trace
Trace is a tool for writing programs which read, write and reason about programs. Some kinds of things you might find Trace useful for:

*   Algorithms which operate on a computation graph, e.g. backpropagation, belief propagation, or other graphical inference algorithms
*   An intermediate data structure for static analysis, interpreters or compilers
*   A general-purpose non-black-box representation of objectives/constraints for optimization
*   A general-purpose non-black-box representation of world models for AI more broadly

Disclaimer for all of these: Trace is brand-new, and it was built with a focus on the core ideas rather than the engineering. Syntax is liable to change as we figure out what does and does not work well. Do not expect it to be easy/pleasant to use at this point, but do expect it to provide novel ways to think about programs. Feedback of all forms is very appreciated!

One more warning: this doc is intended to be read start-to-finish. Trace does not really resemble any other tool I know of, and you will likely be confused if you just dive in.

What is Trace?
--------------

Trace is

*   A programming/modelling language embedded in a python library. For use as a human-facing programming language, Trace is pretty terrible, but it’s sometimes a necessary step for other use-cases.
*   A notation/data structure representing programs. For these use-cases, Trace is pretty good: compared to alternatives (e.g. [abstract syntax trees](https://docs.python.org/3/library/ast.html)), Trace offers a much more convenient representation of program structure.
*   A data structure representing the computation performed by an arbitrary program - i.e. the trace (aka execution graph aka computation graph) of a program. For this use-case, I do not know of any other tool which is anywhere near as powerful as Trace.

A prototypical use-case: suppose you want to test out a new inference algorithm. You can prototype the algorithm to operate on Trace data structures, which allows it to handle arbitrary programs (unlike e.g. pytorch graphs), with relatively little complexity (unlike e.g. python syntax trees). Then, you can write test-case world-models as programs in Trace notation. Those “programs” will themselves be fairly transparent Trace data structures, which your prototype algorithm can operate on directly.

Concepts
--------

Here’s a simple python program:
```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)
```
Let’s suppose I want to trace the execution of factorial(3), starting from the result and working backwards (e.g. for something analogous to backpropagation). Conceptually, I picture something like the call stack, with a box for each function call. Within each box, variable instances are in dependency order; arrows show cross-box dependencies:

![](https://docs.google.com/drawings/u/1/d/sd96WW1-q7XMOjaa4myWWCg/image?w=303&h=580&rev=219&ac=1&parent=11EkEZyVCqIg8JumgL285wDNzMJaYX7mrv-Q4lAoIYv4)

This is roughly the core data structure which Trace exposes. For every instance of every variable, it tells us:

*   The value of the variable-instance
*   The expression which produced that value
*   The variable-instances which went into that expression

(Side note: every variable instance is assumed to be write-once; no in-place updating of values is allowed.)

In Trace syntax, every variable-instance is a Symbol (S). The Symbol object contains both the symbol’s name (aka its literal) and a pointer to the “context” in which the symbol lives (i.e. the dotted boxes in the diagram). The context then assigns the literal to another symbol, a hardcoded value, or an Expression - a special type of Symbol which wraps a python function and some input Symbols. More on that in the next section.

However, Trace’ core data structures differ in two important ways from the diagram above:

*   They handle dynamic structure - i.e. programs which write programs
*   Everything in Trace is evaluated lazily whenever possible

Lazy evaluation allows us to write data structures which _look_ a lot like normal programs (albeit with some unusual syntax), and which can fit in about as much memory as normal code, but allow access to the whole trace - every instance of every variable in the program’s execution.

The main trick to a compressed, lazy representation is an operator which says “make a copy of this whole block, but with these changes: …”. In the factorial diagram above, each of the dotted boxes (except the last) is a copy of the first box, but with a different value of n. Ignoring the last box, we could represent it like this:

![](https://docs.google.com/drawings/u/1/d/sMl-gGQMv8Y-5Kd0y3Cajrg/image?w=303&h=184&rev=71&ac=1&parent=11EkEZyVCqIg8JumgL285wDNzMJaYX7mrv-Q4lAoIYv4)

Here the “?”s represent lazily-evaluated values which haven’t been evaluated yet. Note that the “copy” is nested within the outermost box - indicating that it, too, will be copied, leading to a whole nested ladder of blocks.

In Trace syntax, the dotted boxes are Context objects, and the copy-with-changes operator is represented by function-call notation: `cont({"n":2})` makes a copy of the Context cont, in which "n" is assigned the value 2. Values of variable-instances downstream of n will update in response to the new value of n, within the copy.

Core Data Structure
-------------------

Here’s a full program in Trace; we’re going to walk through all the pieces.
```python
from tracelang import S, E, Context
factorial = Context({
    "fact": Context({
        "result": S(S("n") == 0, {
            True: 1,
            False: S("n")*S("result", S("fact")({"n": S("n") - 1}))
        })
    })({"fact": S("fact")}),
    "result": S("result", S("fact")({"n": S("n")}))
})
```
```python
>>> S("result", factorial({"n": 3})).get_value()
6
```
Let’s start with the three main pieces: Symbols (S), Expressions (E), and Context. Very briefly:

*   A Symbol is a variable-instance. It’s defined by a literal (e.g. "n") and a context in which to resolve that literal (e.g. `{"n": 2}`). Calling get_value() on a symbol resolves the literal within its context.
*   Expressions are Symbols whose “context” is a python function, so we resolve them by calling the function. They are implicitly created by using operators like +, *, ==, or function call on Symbols.
*   Contexts are basically dicts with a couple extra features: they provide a default context for any symbols within them, and we can “create a copy but with changes” via function-call notation.

More details follow...

Symbols are the starting point. A symbol is just a literal (e.g. "foo" or 2) and a context mapping the literal to some value (e.g. `{"foo": "bar"}`; it doesn’t have to be a capital-C Context). By calling `.get_value()` on a symbol, we get the value of the literal from the context:
```python
>>> S("foo", {"foo": "bar", "baz": 2}).get_value()
"bar"
```
Both the literal and the context can themselves be symbols, in which case we resolve values recursively. For instance:
```python
>>> S(S("is_case", {"is_case": True}), {True: "it is", False: "it is not"}).get_value()
"it is"
>>> S("foo", S("bar", {"bar": {"foo": 2}})).get_value()
2
```
Conceptually, `S("x", context)` works like the square-bracket accessor `context["x"]` - except that we recursively resolve symbols along the way.

In our factorial program, notice that many of the symbols don't have any explicit context - e.g. `S("n")` or `S("fact")`. **When a symbol’s context is not explicitly passed, the context is set to the (lexically) enclosing Context** \- this is one of the two main uses of capital-C Contexts. For instance, the `S("n")`'s in our example all have their context set to one of the two Contexts, depending on which one they appear inside.

Expressions are a special type of Symbol which resolve by calling a python function. If we have a function
```python
def square(x):
    return x*x
```
then we could call it via
```python
>>> E(square, S("x", {"x": 2})).get_value()
4
```
This resolves all the input Symbols, then calls the python function, as you’d expect. In practice, we don’t usually need to write E() explicitly - **an E will be created automatically via operator overloading on Symbols**:
```python
>>> total = S("x", {"x":2}) + S("y", {"y":3})
>>> type(total)
E
>>> total.get_value()
5
```
In our factorial program, E’s are implicitly created where we multiply symbols (i.e. `S("n")*S("res", …)`), subtract symbols (i.e. `S("n") - 1`), compare symbols (i.e. `S("n") == 0`), and where we call symbols (i.e. `S("fact")({"n": S("n")})`).

So if they're implicit, why do we need to know all this? Remember, the point of Trace is not merely to "run the code" (i.e. call `.get_value()`), but to query the structure of the computation - and E's are one of the main things which comprise that data structure. We'll see a bit of that in the next section.

Contexts are, conceptually, mostly just dicts. They map things to other things. The two main differences between a context and an ordinary python dict are:

*   If a Symbol doesn’t have an explicit context, its context will be set to the lexically enclosing Context.
*   By calling a Context with a dict, we create a modified copy of the context.

In the example program, we create a modified copy in three places:

*   `S("fact")({"n": S("n") - 1})` creates a copy of the context called "fact" for the recursive call, just like the diagram from the previous section.
*   `Context({...})({"fact": S("fact")})` is used to pass a pointer to the fact-context inside of the fact-context itself, so copies can be made.
*   `S("fact")({"n": S("n")})` is just a pass-through function call.

When actually using the factorial function, we create one more modified copy: `factorial({"n": 3})`. This is the first copy with a value actually assigned to "n".

Before we jump back in to our factorial example, let’s see how these pieces play together in a simpler example:
```python
import operator as op
half_adder = Context({
    "a": 0,
    "b": 1,
    "sum": E(op.xor, [S("a"), S("b")]),
    "carry": E(op.and_, [S("a"), S("b")])
})
```
This example contains two Symbols (other than the E’s). Neither Symbol has an explicit context passed, so both have their context set to the enclosing Context - i.e. the object half\_adder. To get value of "sum" within half\_adder, we’d call `S("sum", half_adder).get_value()`. This would look up the values of `S("a", half_adder)` and `S("b", half_adder)`, then pass those values to the python function `op.xor`. We could also evaluate at other inputs by making a modified copy - e.g. `half_adder({"a": 1, "b": 0})`.

That’s all the core pieces. Let’s take another look at our example program:
```python
from tracelang import S, E, Context
factorial = Context({
    "fact": Context({
        "result": S(S("n") == 0, {
            True: 1,
            False: S("n")*S("result", S("fact")({"n": S("n") - 1}))
        })
    })({"fact": S("fact")}),
    "result": S("result", S("fact")({"n": S("n")}))
})
```
```python
>>> S("result", factorial({"n": 3})).get_value()
6
```

We have two Contexts. The inner Context is our main function, but we need to use the outer Context in order to get a pointer to the inner context, so that we can make modified copies of it. There’s some code patterns which are probably unfamiliar at this point - e.g. `S(S("n") == 0, …)` is used to emulate an if-statement, and we write things like `S("result", fact)` rather than `fact["result"]`. But overall, hopefully the underlying structure of this code looks familiar.

But if all we wanted to do was write and run code, we wouldn’t be using Trace in the first place. Let’s probe our program a bit.

Stepping Through the Code
-------------------------

Human programmers sometimes “step through the code”, following the execution step-by-step to better understand what’s going on. IDEs often provide tools to help with this (e.g. breakpoints), but most programming languages don’t offer a nice way to step through the code programmatically. For Trace, this is a simple - and fundamental - use-case.

Here’s how we step through some Trace code.

We start with our final output, e.g. `answer = S("result", factorial({"n": 3}))`. Before, we called `answer.get_value()` on this object, but now we won’t. Instead, we’ll access the pieces which went into that Symbol: `answer._literal`, and `answer._context`. In general, we can “work backwards” in three possible “directions”:

*   If `answer._literal` is a Symbol/Expression, then we can step back through it, and/or we can get its value
*   If `answer._context` is a Symbol/Expression, then we can step back through it, and/or we can get its value
*   Once we have both values, we can look up `answer._context[answer._literal]` to find the Symbol/Expression/Value defining answer in its context.

In this case, the literal is not a Symbol, but the context is - it’s an Expression object, which performs the modified-copy operation on our factorial context. By calling `answer._context.get_value()`, we get a new Context, which is a copy of factorial with the modification `{n: 3}` applied. By looking at the Expression object itself, we can see the original factorial context and the `{n: 3}`: `answer._context._literal` is a list containing `factorial` and `{n: 3}`.

Let’s go one step further in: we’ll set `last_step = answer._context.get_value()\[answer._literal]`, and look at `last_step`.

Now we get an object which looks like `S("result", S("fact", <modified copy>)({"n": S("n", <modified copy>)}))`, where the modified copy is the copy of factorial with `{n: 3}` applied. The outermost symbol once again has a string as literal, and its context is an Expression object performing the modified-copy operation on a Context. Calling `.get_value()` on the Expression `last_step._context` would lead us even further in.

Now, obviously this is not a very convenient way for a _human_ to trace through a program’s execution. But if we want to write _programs_ which trace through other programs’ execution, then this looks more reasonable - there’s a relatively small number of possibilities to check at every step, a relatively small number of object types to handle, and we have a data structure which lets us walk through the entire program trace.

Definitely Real User Testimony
------------------------------

To wrap it up, here are some endorsements from enthusiastic Trace users.

“Trace is an AI-oriented programming language for people who like Lisp, but think it doesn't go far enough.” - Ada Lovelace

“Isn’t this just math?” - Charles Babbage

“Trace combines the syntax of JSON with the semantics of a spreadsheet, but instead of just ending up horrendously hackish, it ends up horrendously abstract _and_ horrendously hackish.” - John Von Neumann

“In Trace, source code is truly just data, always.” - Alan Turing

Installation
------------

Run `python3 setup install` to use or `python3 setup develop ` if you want to modify the package.