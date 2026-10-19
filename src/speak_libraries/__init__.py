"""Speak libraries: well-known Python libraries re-described in plain, unabbreviated English.

In a Speak program:

    use numpy
    use micromelon as robot

`use` loads the Speak version of the library if there is one (so you write
`numpy.standard_deviation(numbers)` instead of `np.std(numbers)`). For any other
installed Python library, `use` gives you the ordinary library.
Each Speak library has a `raw` value holding the original Python library, and
`list_functions()` which prints everything it offers.
"""
import importlib
import inspect
import sys

AVAILABLE = ('math', 'random', 'time', 'numpy', 'pandas', 'matplotlib', 'micromelon')


def describe(module):
    """Prints each public function of a Speak library with its one-line description."""
    rows = []
    for name, thing in sorted(vars(module).items()):
        if name.startswith('_') or not inspect.isfunction(thing) or thing.__module__ != module.__name__:
            continue
        if name == 'list_functions':
            continue
        summary = (inspect.getdoc(thing) or '').split('\n')[0]
        rows.append((f'{name}{inspect.signature(thing)}', summary))
    width = max((len(signature) for signature, _ in rows), default=0)
    for signature, summary in rows:
        print(f'{signature.ljust(width)}  {summary}')


def load(name):
    """Returns the Speak version of a library, or the ordinary Python library of that name."""
    if name in AVAILABLE:
        module = importlib.import_module(f'speak_libraries.speak_{name}')
        module.list_functions = lambda: describe(module)
        return module
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        raise ValueError(
            f'I do not know a library called "{name}". Speak has its own versions of: '
            f'{", ".join(AVAILABLE)}. Other installed Python libraries also work with "use" or "import".'
        ) from None
