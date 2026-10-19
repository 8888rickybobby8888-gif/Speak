#!/usr/bin/env python3
"""Speak: a readable pseudocode language that compiles to Python.

Because a Speak program becomes Python, any Python library works:
    import numpy as np
    print np.mean(np.array([1, 2, 3]))
"""
import ast
import builtins
import difflib
import json
import keyword
import math
import numbers
import os
import random
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # lets "use" find speak_libraries


class SpeakError(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.line = line


# ---------------------------------------------------------------- tokenizer

class Token:
    __slots__ = ('kind', 'value', 'lower')

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
        self.lower = value.lower() if kind == 'word' else ''


NUMBER = re.compile(r'\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
WORD = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
SYMBOL = re.compile(r'\*\*|//|\+=|-=|\*=|/=|!=|<>|==|<=|>=|[-+*/%@=<>,()\[\]{}:.≠≤≥←×÷]')
# Other ways pseudocode writes the same thing.
SYMBOL_ALIASES = {'<>': '!=', '==': '=', '≠': '!=', '≤': '<=', '≥': '>=', '←': '<-', '×': '*', '÷': '/'}


def tokenize(text, line):
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == '#':
            break  # a comment runs to the end of the line
        if text.startswith('<-', i) and (i == 0 or text[i - 1].isspace()) and text[i + 2:i + 3] in ('', ' ', '\t'):
            tokens.append(Token('symbol', '<-'))  # assignment arrow, as in: total <- 5
            i += 2
            continue
        if c == '"':
            value = []
            i += 1
            while i < len(text) and text[i] != '"':
                if text[i] == '\\' and i + 1 < len(text):
                    n = text[i + 1]
                    value.append({'n': '\n', 't': '\t', '(': '\x01'}.get(n, n))  # \x01 marks a literal "\("
                    i += 2
                else:
                    value.append(text[i])
                    i += 1
            if i >= len(text):
                raise SpeakError('This text is missing its closing quote mark.', line)
            i += 1
            tokens.append(Token('text', ''.join(value)))
            continue
        for kind, pattern in (('number', NUMBER), ('word', WORD), ('symbol', SYMBOL)):
            m = pattern.match(text, i)
            if m:
                tokens.append(Token(kind, SYMBOL_ALIASES.get(m.group(), m.group()) if kind == 'symbol' else m.group()))
                i = m.end()
                break
        else:
            raise SpeakError(f'I do not understand the character "{c}".', line)
    return tokens


class Cursor:
    def __init__(self, tokens, line):
        self.tokens = tokens
        self.i = 0
        self.line = line

    @property
    def done(self):
        return self.i >= len(self.tokens)

    def peek(self, offset=0):
        k = self.i + offset
        return self.tokens[k] if k < len(self.tokens) else None

    def fail(self, message):
        raise SpeakError(message, self.line)

    def found(self):
        t = self.peek()
        return f' but found "{t.value}"' if t else ' but the line ended'

    def is_word(self, word, offset=0):
        t = self.peek(offset)
        return t is not None and t.kind == 'word' and t.lower == word

    def is_sequence(self, *words):
        return all(self.is_word(w, k) for k, w in enumerate(words))

    def accept_sequence(self, *words):
        if self.is_sequence(*words):
            self.i += len(words)
            return True
        return False

    def expect_sequence(self, *words):
        if not self.accept_sequence(*words):
            self.fail(f'I expected "{" ".join(words)}" here{self.found()}.')

    def is_symbol(self, symbol, offset=0):
        t = self.peek(offset)
        return t is not None and t.kind == 'symbol' and t.value == symbol

    def accept_symbol(self, symbol):
        if self.is_symbol(symbol):
            self.i += 1
            return True
        return False

    def expect_symbol(self, symbol):
        if not self.accept_symbol(symbol):
            self.fail(f'I expected "{symbol}" here{self.found()}.')

    def name(self):
        t = self.peek()
        if t is None or t.kind != 'word':
            self.fail(f'I expected a name here{self.found()}.')
        self.i += 1
        check_name(t.value, self)
        return t.value

    def expect_end(self):
        if not self.done:
            self.fail(f'I did not expect "{self.peek().value}" here.')


PYTHON_RESERVED = set(keyword.kwlist) - {'True', 'False', 'None'}
SPEAK_RESERVED = {'then', 'otherwise', 'with', 'of', 'to', 'by', 'each', 'contains'}


def check_name(name, cur):
    if name in PYTHON_RESERVED:
        cur.fail(f'"{name}" is a reserved word and cannot be used as a name here.')


# --------------------------------------------------- expressions -> Python

def parse_expression(cur):
    return parse_or(cur)


def parse_or(cur):
    left = parse_and(cur)
    while cur.accept_sequence('or'):
        left = f'({left} or {parse_and(cur)})'
    return left


def parse_and(cur):
    left = parse_not(cur)
    while cur.accept_sequence('and'):
        left = f'({left} and {parse_not(cur)})'
    return left


def parse_not(cur):
    if cur.accept_sequence('not'):
        return f'(not {parse_not(cur)})'
    return parse_comparison(cur)


COMPARISONS = {'!=': '!=', '<=': '<=', '>=': '>=', '=': '==', '<': '<', '>': '>'}


# The same comparisons written as words. Longest phrases first.
WORD_COMPARISONS = [
    (('is', 'greater', 'than', 'or', 'equal', 'to'), '>='),
    (('is', 'less', 'than', 'or', 'equal', 'to'), '<='),
    (('is', 'not', 'equal', 'to'), '!='),
    (('is', 'equal', 'to'), '=='),
    (('is', 'greater', 'than'), '>'),
    (('is', 'less', 'than'), '<'),
    (('is', 'at', 'least'), '>='),
    (('is', 'at', 'most'), '<='),
    (('is', 'not'), '!='),
    (('is',), '=='),
    (('equals',), '=='),
]


def parse_comparison(cur):
    left = parse_sum(cur)
    t = cur.peek()
    if t is not None and t.kind == 'symbol' and t.value in COMPARISONS:
        cur.i += 1
        return f'({left} {COMPARISONS[t.value]} {parse_sum(cur)})'
    if cur.accept_sequence('contains'):
        return f'({parse_sum(cur)} in {left})'
    if cur.accept_sequence('does', 'not', 'contain'):
        return f'({parse_sum(cur)} not in {left})'
    for words, op in WORD_COMPARISONS:
        if cur.accept_sequence(*words):
            return f'({left} {op} {parse_sum(cur)})'
    return left


def parse_sum(cur):
    left = parse_product(cur)
    while True:
        if cur.is_symbol('+') or cur.accept_sequence('plus'):
            op = '+'
            if cur.is_symbol('+'):
                cur.i += 1
        elif cur.is_symbol('-') or cur.accept_sequence('minus'):
            op = '-'
            if cur.is_symbol('-'):
                cur.i += 1
        else:
            return left
        right = parse_product(cur)
        left = f'_plus({left}, {right})' if op == '+' else f'({left} - {right})'


def parse_product(cur):
    left = parse_unary(cur)
    while True:
        t = cur.peek()
        if t is not None and t.kind == 'symbol' and t.value in ('*', '/', '//', '%', '@'):
            cur.i += 1
            op = t.value
        # "repeat 3 times" ends a line with "times", so only multiply when a value follows.
        elif cur.is_word('times') and cur.peek(1) is not None and not cur.is_word('do', 1):
            cur.i += 1
            op = '*'
        elif cur.accept_sequence('multiplied', 'by'):
            op = '*'
        elif cur.accept_sequence('divided', 'by'):
            op = '/'
        elif cur.accept_sequence('modulo'):
            op = '%'
        else:
            return left
        left = f'({left} {op} {parse_unary(cur)})'


def parse_unary(cur):
    if cur.accept_symbol('-'):
        return f'(-{parse_unary(cur)})'
    base = parse_postfix(cur)
    if cur.accept_symbol('**') or cur.accept_sequence('to', 'the', 'power', 'of'):
        return f'({base} ** {parse_unary(cur)})'
    return base


def parse_call_arguments(cur, closing=None):
    """Arguments for a call. Supports name=value for keyword arguments."""
    args = []
    if cur.done or (closing and cur.is_symbol(closing)):
        return ''
    while True:
        t, nxt = cur.peek(), cur.peek(1)
        if t.kind == 'word' and nxt is not None and nxt.kind == 'symbol' and nxt.value == '=':
            cur.i += 2
            args.append(f'{t.value}={parse_or(cur)}')
        else:
            args.append(parse_or(cur))
        if not cur.accept_symbol(','):
            break
    return ', '.join(args)


def parse_index(cur):
    """Everything inside [...]: positions, slices (a:b:c) and numpy-style a, b."""
    dims = []
    while True:
        parts = ['']
        while True:
            if cur.is_symbol(':'):
                cur.i += 1
                parts.append('')
            elif cur.is_symbol(',') or cur.is_symbol(']'):
                break
            else:
                parts[-1] = parse_or(cur)
        dims.append(':'.join(parts))
        if not cur.accept_symbol(','):
            break
    cur.expect_symbol(']')
    return ', '.join(dims)


def parse_postfix(cur, allow_call=True):
    expr = parse_primary(cur)
    while True:
        if cur.is_symbol('.') and cur.peek(1) is not None and cur.peek(1).kind == 'word':
            expr = f'{expr}.{cur.peek(1).value}'
            cur.i += 2
        elif allow_call and cur.is_symbol('('):
            cur.i += 1
            args = parse_call_arguments(cur, ')')
            cur.expect_symbol(')')
            expr = f'{expr}({args})'
        elif cur.is_symbol('['):
            cur.i += 1
            expr = f'{expr}[{parse_index(cur)}]'
        else:
            return expr


BUILTINS = {
    'length': 'len({})',
    'uppercase': 'str({}).upper()',
    'lowercase': 'str({}).lower()',
    'round': 'round({})',
    'absolute value': 'abs({})',
    'square root': '_math.sqrt({})',
    'text version': '_show({})',
    'number version': '_number({})',
}


def parse_primary(cur):
    t = cur.peek()
    if t is None:
        cur.fail('The line ended but I expected a value.')
    if t.kind == 'number':
        cur.i += 1
        return t.value
    if t.kind == 'text':
        cur.i += 1
        return filled_text(t.value) if FILL_IN_TEXT[0] else repr(t.value.replace('\x01', '('))
    if t.kind == 'symbol':
        if t.value == '(':
            cur.i += 1
            items = [parse_or(cur)]
            is_tuple = False
            while cur.accept_symbol(','):
                is_tuple = True
                if cur.is_symbol(')'):
                    break
                items.append(parse_or(cur))
            cur.expect_symbol(')')
            return '(' + ', '.join(items) + (',' if is_tuple and len(items) == 1 else '') + ')'
        if t.value == '[':
            cur.i += 1
            items = parse_call_arguments(cur, ']')
            cur.expect_symbol(']')
            return f'[{items}]'
        if t.value == '{':
            cur.i += 1
            pairs = []
            while not cur.is_symbol('}'):
                key = parse_or(cur)
                cur.expect_symbol(':')
                pairs.append(f'{key}: {parse_or(cur)}')
                if not cur.accept_symbol(','):
                    break
            cur.expect_symbol('}')
            return '{' + ', '.join(pairs) + '}'
        cur.fail(f'I did not expect "{t.value}" here.')
    # a word
    if cur.accept_sequence('true'):
        return 'True'
    if cur.accept_sequence('false'):
        return 'False'
    if cur.accept_sequence('nothing'):
        return 'None'
    if cur.accept_sequence('an', 'empty', 'list'):
        return '[]'
    if cur.accept_sequence('a', 'list', 'of'):
        return f'[{parse_call_arguments(cur)}]'
    if cur.accept_sequence('call'):
        callee = parse_postfix(cur, allow_call=False)
        if callee == 'super()':
            callee = 'super().__init__'
        args = parse_call_arguments(cur) if cur.accept_sequence('with') else ''
        return f'{callee}({args})'
    if cur.accept_sequence('create'):
        callee = parse_postfix(cur, allow_call=False)
        args = parse_call_arguments(cur) if cur.accept_sequence('with') else ''
        return f'{callee}({args})'
    if cur.accept_sequence('parent'):
        return 'super()'
    if cur.is_word('item') and cur.peek(1) is not None and not cur.is_word('of', 1) \
            and not (cur.peek(1).kind == 'symbol' and cur.peek(1).value in ('=', '.', ')', ',')):
        cur.i += 1
        position = parse_sum(cur)
        cur.expect_sequence('of')
        return f'_item({parse_unary(cur)}, {position})'
    if cur.accept_sequence('random', 'number', 'from'):
        low = parse_sum(cur)
        cur.expect_sequence('to')
        return f'_random.randint({low}, {parse_sum(cur)})'
    for phrase, template in BUILTINS.items():
        words = phrase.split() + ['of']
        if cur.is_sequence(*words):
            cur.i += len(words)
            return template.format(parse_unary(cur))
    if t.lower in SPEAK_RESERVED:
        cur.fail(f'I did not expect "{t.value}" here.')
    cur.i += 1
    check_name(t.value, cur)
    return t.value


FILL_IN_TEXT = [False]  # True while compiling the text of print and ask


def filled_text(text):
    """Python for a text literal in which (name) or (expression) is replaced by its value.

    Only brackets holding a valid expression that uses a name are treated this way, and only when the
    name exists when the line runs: "(yes or no)" and "Press (1) to start" stay as written.
    Write \\( to keep a bracket that would otherwise be filled in.
    """
    parts, literal, i = [], [], 0
    while i < len(text):
        if text[i] == '(':
            depth, j = 0, i
            while j < len(text):
                depth += (text[j] == '(') - (text[j] == ')')
                if depth == 0:
                    break
                j += 1
            if j < len(text):
                inner = text[i + 1:j]
                expression = fill_expression(inner)
                if expression is not None:
                    if literal:
                        parts.append(repr(''.join(literal)))
                        literal = []
                    parts.append(f'({text[i:j + 1]!r}, lambda: ({expression}))')
                    i = j + 1
                    continue
        literal.append(text[i])
        i += 1
    if not parts:
        return repr(text.replace('\x01', '('))
    if literal:
        parts.append(repr(''.join(literal)))
    return '_fill([' + ', '.join(parts).replace('\\x01', '(') + '])'


def fill_expression(inner):
    """Python for the inside of a (bracket) in text, or None if it should stay as written."""
    try:
        tokens = tokenize(inner, 0)
        if not any(t.kind == 'word' and t.lower not in ('true', 'false', 'nothing') for t in tokens):
            return None  # numbers and symbols only, like (1) or (2 + 3): leave it alone
        return compile_expression(inner)
    except SpeakError:
        return None


def parse_value_list(cur):
    items = [parse_or(cur)]
    while cur.accept_symbol(','):
        items.append(parse_or(cur))
    return ', '.join(items)


# ---------------------------------------------------- statements -> Python

class Line:
    def __init__(self, tokens, number, indent=0):
        self.tokens = tokens
        self.number = number
        self.indent = indent


ASSIGNMENT_OPERATORS = ('=', '<-', '+=', '-=', '*=', '/=')
END_KINDS = {'if', 'while', 'for', 'repeat', 'function', 'procedure', 'class', 'when', 'loop'}
# Words that start a statement but can still be used as ordinary names: output = 5
SOFT_WORDS = {'output', 'display', 'input', 'set', 'let', 'increase', 'decrease', 'function', 'procedure',
              'end', 'next', 'until', 'subtract', 'multiply', 'divide', 'swap', 'local'}
CLOSERS = {'end', 'otherwise', 'else', 'until', 'next'}


def top_level_else(tokens):
    """Where an "else" or "otherwise" sits in the rest of a one-line if, or None."""
    depth = 0
    for index, token in enumerate(tokens):
        if token.kind == 'symbol' and token.value in '([{':
            depth += 1
        elif token.kind == 'symbol' and token.value in ')]}':
            depth -= 1
        elif depth == 0 and token.kind == 'word' and token.lower in ('else', 'otherwise'):
            return index
    return None


def line_head(line):
    """The first two lowercase words of a line, with "endif" read as "end if"."""
    first = line.tokens[0]
    if first.kind == 'word' and first.lower.startswith('end') and first.lower[3:] in END_KINDS:
        return ['end', first.lower[3:]]
    return [t.lower for t in line.tokens[:2]]


OPENERS = {'if', 'while', 'for', 'repeat', 'define', 'function', 'procedure', 'when', 'class'}


class Compiler:
    def __init__(self, lines, errors=None):
        self.errors = errors  # None: stop at the first problem. A list: collect every problem found.
        self.skip_indent = None
        self.lines = lines
        self.indents = {line.number: line.indent for line in lines}
        self.position = 0
        self.depth = 0
        self.class_bodies = []  # indentation depths that are directly inside a class
        self.out = []  # (python text, speak line number)

    def emit(self, text, line):
        self.out.append(('    ' * self.depth + text, line))

    def run(self):
        while self.position < len(self.lines):
            line = self.lines[self.position]
            self.position += 1
            self.run_statement(line)

    def run_statement(self, line):
        """Compiles one statement. When collecting problems, a bad statement is recorded and skipped."""
        if self.errors is None:
            self.statement(line)
            return
        if self.skip_indent is not None:
            if line.indent > self.skip_indent:
                return  # inside a block whose first line was already reported
            self.skip_indent = None
        depth, size, classes = self.depth, len(self.out), list(self.class_bodies)
        try:
            self.statement(line)
        except SpeakError as error:
            self.depth, self.class_bodies = depth, classes
            del self.out[size:]
            if 'has nothing to close' in str(error) and self.errors:
                return  # most likely a knock-on effect of an earlier problem
            self.errors.append(error)
            following = self.lines[self.position] if self.position < len(self.lines) else None
            if following is not None and following.indent > line.indent:
                self.skip_indent = line.indent

    def block(self, endings, opener):
        """Compile an indented block; returns (ending phrase, its line).

        The block normally stops at one of the `endings` lines (such as "end if").
        If its body is indented, it also stops, with (None, None), at the first line
        that is no longer indented more than the line that opened it, or at the end
        of the file. So the "end ..." line is optional in well-indented code.
        """
        self.depth += 1
        start = len(self.out)
        opener_indent = self.indents.get(opener, 0)
        indented = None
        while self.position < len(self.lines):
            line = self.lines[self.position]
            head = line_head(line)
            for ending in endings:
                words = ending.split()
                if head[:len(words)] == words:
                    self.position += 1
                    if len(self.out) == start:
                        self.emit('pass', line.number)
                    self.depth -= 1
                    return ending, line
            if indented is None:
                indented = line.indent > opener_indent
            elif indented and line.indent <= opener_indent:
                self.depth -= 1
                return None, None
            self.position += 1
            self.run_statement(line)
        if indented:
            self.depth -= 1
            return None, None
        error = SpeakError(f'This block is never closed. Add "{endings[-1]}" after its last line.', opener)
        if self.errors is None:
            raise error
        self.errors.append(error)
        self.depth -= 1
        return None, None

    def statement(self, line):
        cur = Cursor(line.tokens, line.number)
        first = cur.peek()
        word = first.lower if first.kind == 'word' else ''
        second = cur.peek(1)
        assigning = second is not None and second.kind == 'symbol' and \
            (second.value in ASSIGNMENT_OPERATORS or second.value == '.')
        if word and not (assigning and word in SOFT_WORDS):
            handler = getattr(self, 'do_' + word, None)
            if handler and word in STATEMENT_WORDS:
                cur.i += 1
                handler(cur, line.number)
                return
            if word in CLOSERS or (word.startswith('end') and word[3:] in END_KINDS):
                cur.fail(f'"{first.value}" has nothing to close here.')
        self.assignment_or_expression(cur, line.number)

    # -- simple statements

    def do_print(self, cur, at):
        FILL_IN_TEXT[0] = True
        try:
            self.print_statement(cur, at)
        finally:
            FILL_IN_TEXT[0] = False

    def print_statement(self, cur, at):
        if cur.is_symbol('('):
            start = cur.i
            cur.i += 1
            args = parse_call_arguments(cur, ')')
            if cur.accept_symbol(')') and cur.done:
                self.emit(f'_print({args})', at)
                return
            cur.i = start
        args = '' if cur.done else parse_value_list(cur)
        cur.expect_end()
        self.emit(f'_print({args})', at)

    do_output = do_print
    do_display = do_print

    def do_set(self, cur, at):
        if cur.is_word('item') and not cur.is_word('to', 1):
            cur.i += 1
            position = parse_sum(cur)
            cur.expect_sequence('of')
            target = parse_postfix(cur)
            cur.expect_sequence('to')
            value = parse_expression(cur)
            cur.expect_end()
            self.emit(f'_set_item({target}, {position}, {value})', at)
            return
        targets = [parse_postfix(cur)]
        while cur.accept_symbol(','):
            targets.append(parse_postfix(cur))
        cur.expect_sequence('to')
        value = parse_value_list(cur)
        cur.expect_end()
        self.emit(f'{", ".join(targets)} = {value}', at)

    def change_by(self, cur, at, sign):
        target = parse_postfix(cur)
        amount = parse_sum(cur) if cur.accept_sequence('by') else '1'
        cur.expect_end()
        self.emit(f'{target} {sign}= {amount}', at)

    def do_increase(self, cur, at):
        self.change_by(cur, at, '+')

    def do_decrease(self, cur, at):
        self.change_by(cur, at, '-')

    def do_input(self, cur, at):
        if cur.peek() is not None and cur.peek().kind == 'word' and cur.peek(1) is None:
            name = cur.name()
            self.emit(f'{name} = _ask("", {name!r}, {at})', at)  # input answer
        else:
            self.do_ask(cur, at)  # input "Question?" store as answer

    def declare_scope(self, cur, at, kind):
        names = [cur.name()]
        while cur.accept_symbol(','):
            names.append(cur.name())
        cur.expect_end()
        # A note to the scope pass (declare_outer_variables); harmless when the program runs.
        self.emit(repr(f'{kind}: {", ".join(names)}'), at)

    def do_global(self, cur, at):
        self.declare_scope(cur, at, 'global')

    def do_local(self, cur, at):
        self.declare_scope(cur, at, 'local')

    def do_ask(self, cur, at):
        FILL_IN_TEXT[0] = True
        try:
            prompt = parse_sum(cur)
        finally:
            FILL_IN_TEXT[0] = False
        cur.expect_sequence('store', 'as')
        name = cur.name()
        cur.expect_end()
        self.emit(f'{name} = _ask({prompt}, {name!r}, {at})', at)

    def do_add(self, cur, at):
        value = parse_or(cur)
        cur.expect_sequence('to')
        target = parse_postfix(cur)
        cur.expect_end()
        self.emit(f'{target} = _add({target}, {value})', at)

    def do_subtract(self, cur, at):
        value = parse_or(cur)
        cur.expect_sequence('from')
        target = parse_postfix(cur)
        cur.expect_end()
        self.emit(f'{target} -= {value}', at)

    def do_multiply(self, cur, at):
        target = parse_postfix(cur)
        cur.expect_sequence('by')
        value = parse_or(cur)
        cur.expect_end()
        self.emit(f'{target} *= {value}', at)

    def do_divide(self, cur, at):
        target = parse_postfix(cur)
        cur.expect_sequence('by')
        value = parse_or(cur)
        cur.expect_end()
        self.emit(f'{target} /= {value}', at)

    def do_swap(self, cur, at):
        first = parse_postfix(cur)
        cur.expect_sequence('and')
        second = parse_postfix(cur)
        cur.expect_end()
        self.emit(f'{first}, {second} = {second}, {first}', at)

    def do_let(self, cur, at):
        targets = [parse_postfix(cur)]
        while cur.accept_symbol(','):
            targets.append(parse_postfix(cur))
        if not (cur.accept_sequence('be') or cur.accept_symbol('=')):
            cur.fail(f'I expected "be" here{cur.found()}.')
        value = parse_value_list(cur)
        cur.expect_end()
        self.emit(f'{", ".join(targets)} = {value}', at)

    def do_remove(self, cur, at):
        cur.expect_sequence('item')
        position = parse_sum(cur)
        cur.expect_sequence('from')
        target = parse_postfix(cur)
        cur.expect_end()
        self.emit(f'_remove_item({target}, {position})', at)

    def do_return(self, cur, at):
        value = '' if cur.done else ' ' + parse_value_list(cur)
        cur.expect_end()
        self.emit(f'return{value}', at)

    def do_stop(self, cur, at):
        cur.expect_sequence('looping')
        cur.expect_end()
        self.emit('break', at)

    def do_skip(self, cur, at):
        cur.expect_sequence('to', 'next', 'round')
        cur.expect_end()
        self.emit('continue', at)

    def do_use(self, cur, at):
        lines = []
        while True:
            library = cur.name()
            alias = cur.name() if cur.accept_sequence('as') else library
            lines.append(f'{alias} = _use({library!r})')
            if not cur.accept_symbol(','):
                break
        cur.expect_end()
        for text in lines:
            self.emit(text, at)

    def do_import(self, cur, at):
        parts = []
        while True:
            module = dotted_name(cur)
            alias = f' as {cur.name()}' if cur.accept_sequence('as') else ''
            parts.append(module + alias)
            if not cur.accept_symbol(','):
                break
        cur.expect_end()
        self.emit('import ' + ', '.join(parts), at)

    def do_from(self, cur, at):
        module = dotted_name(cur)
        cur.expect_sequence('import')
        if cur.accept_symbol('*'):
            cur.expect_end()
            self.emit(f'from {module} import *', at)
            return
        names = []
        while True:
            name = cur.name()
            names.append(name + (f' as {cur.name()}' if cur.accept_sequence('as') else ''))
            if not cur.accept_symbol(','):
                break
        cur.expect_end()
        self.emit(f'from {module} import {", ".join(names)}', at)

    # -- blocks

    def do_if(self, cur, at):
        condition = parse_expression(cur)
        cur.accept_sequence('then')
        self.emit(f'if {condition}:', at)
        ending, terminator = self.if_branch(cur, at)
        while ending is not None:
            after = Cursor(terminator.tokens, terminator.number)
            after.i = 1
            if after.accept_sequence('if'):
                condition = parse_expression(after)
                after.accept_sequence('then')
                self.emit(f'elif {condition}:', terminator.number)
                ending, terminator = self.if_branch(after, at)
            else:
                self.emit('else:', terminator.number)
                self.if_branch(after, at, last=True)
                return

    def if_branch(self, cur, at, last=False):
        """Compiles what follows an if / else if / else. Returns (word, line) when another branch follows.

        The body can be on the same line ("if x > 3 then print "big""), an indented block,
        or, with no "end if" anywhere to close it, just the single statement on the next line.
        """
        if not cur.done:  # one-line form, optionally with its own "else" on the same line
            rest = cur.tokens[cur.i:]
            split = None if last else top_level_else(rest)
            body = rest if split is None else rest[:split]
            if not body:
                cur.fail('I expected something to do here.')
            self.depth += 1
            self.statement(Line(body, cur.line))
            self.depth -= 1
            if split is not None:
                return rest[split].lower, Line(rest[split:], cur.line)
            return (None, None) if last else self.following_else(at)
        opener_indent = self.indents.get(at, 0)
        following = self.lines[self.position] if self.position < len(self.lines) else None
        if following is not None and following.indent <= opener_indent and not self.if_has_end(opener_indent):
            self.position += 1  # no "end if" and no indented body: the next line is the whole body
            self.depth += 1
            self.statement(following)
            self.depth -= 1
            return (None, None) if last else self.following_else(at)
        ending, terminator = self.block(['end if'] if last else ['otherwise', 'else', 'end if'], at)
        return (ending, terminator) if ending in ('otherwise', 'else') else (None, None)

    def following_else(self, at):
        """If the next line is an else that lines up with this if, takes it and returns (word, line)."""
        if self.position < len(self.lines):
            line = self.lines[self.position]
            head = line_head(line)
            if head[0] in ('otherwise', 'else') and line.indent >= self.indents.get(at, 0):
                self.position += 1
                return head[0], line
        return None, None

    def if_has_end(self, opener_indent):
        """Is there an "end if" further on that closes this if? Used to decide how to read an unindented body."""
        depth = 1
        for line in self.lines[self.position:]:
            if line.indent < opener_indent:
                return False  # a block around this one has ended
            head = line_head(line)
            if head[:2] == ['end', 'if']:
                depth -= 1
                if depth == 0:
                    return True
            elif head[0] == 'if' and self.is_block_if(line):
                depth += 1
        return False

    @staticmethod
    def is_block_if(line):
        """True for an if line with its body on the lines below (not the one-line form)."""
        try:
            cur = Cursor(line.tokens, line.number)
            cur.i = 1
            parse_expression(cur)
            cur.accept_sequence('then')
            return cur.done
        except SpeakError:
            return True

    def do_repeat(self, cur, at):
        if cur.done:
            self.repeat_until(at)
            return
        count = parse_expression(cur)
        cur.expect_sequence('times')
        cur.accept_sequence('do')
        cur.expect_end()
        self.emit(f'for _round in range({count}):', at)
        self.block(['end repeat'], at)

    def repeat_until(self, at):
        """repeat ... until condition: the body runs once before the condition is first checked."""
        flag = f'_again{at}'
        self.emit(f'{flag} = True', at)
        index = len(self.out)
        self.emit('while True:', at)  # rewritten below, once the "until" condition is known
        self.depth += 1
        self.emit(f'{flag} = False', at)
        self.depth -= 1
        ending, terminator = self.block(['until'], at)
        if ending != 'until':
            raise SpeakError('This "repeat" needs an "until" line to finish it.', at)
        after = Cursor(terminator.tokens, terminator.number)
        after.i = 1
        condition = parse_expression(after)
        after.expect_end()
        text = self.out[index][0].replace('while True:', f'while {flag} or not ({condition}):')
        self.out[index] = (text, at)

    def do_while(self, cur, at):
        condition = parse_expression(cur)
        cur.accept_sequence('do')
        cur.expect_end()
        self.emit(f'while {condition}:', at)
        self.block(['end while'], at)

    def do_for(self, cur, at):
        if cur.accept_sequence('each'):
            name = cur.name()
            cur.expect_sequence('in')
            source = parse_expression(cur)
            cur.accept_sequence('do')
            cur.expect_end()
            self.emit(f'for {name} in {source}:', at)
        else:
            name = cur.name()
            cur.expect_sequence('from')
            start = parse_sum(cur)
            cur.expect_sequence('to')
            stop = parse_sum(cur)
            step = parse_sum(cur) if cur.accept_sequence('by') else '1'
            cur.accept_sequence('do')
            cur.expect_end()
            self.emit(f'for {name} in _count({start}, {stop}, {step}):', at)
        self.block(['next', 'end for'], at)

    def do_define(self, cur, at):
        if cur.accept_sequence('class'):
            self.define_class(cur, at)
            return
        if not cur.accept_sequence('procedure'):
            cur.expect_sequence('function')
        self.define_function(cur, at)

    def do_function(self, cur, at):
        self.define_function(cur, at)

    do_procedure = do_function

    def define_function(self, cur, at):
        name = cur.name()
        parameters = self.parameter_list(cur)
        cur.expect_end()
        if self.depth in self.class_bodies:
            parameters.insert(0, 'this')
        self.emit(f'def {name}({", ".join(parameters)}):', at)
        self.block(['end procedure', 'end function'], at)

    def parameter_list(self, cur):
        """The values a function takes: "with a, b" or "(a, b)"."""
        parameters = []
        if cur.accept_symbol('('):
            if not cur.accept_symbol(')'):
                parameters.append(cur.name())
                while cur.accept_symbol(','):
                    parameters.append(cur.name())
                cur.expect_symbol(')')
        elif cur.accept_sequence('with'):
            parameters.append(cur.name())
            while cur.accept_symbol(','):
                parameters.append(cur.name())
        return parameters

    def define_class(self, cur, at):
        name = cur.name()
        bases = ''
        if cur.accept_sequence('extends'):
            names = [dotted_name(cur)]
            while cur.accept_symbol(','):
                names.append(dotted_name(cur))
            bases = '(' + ', '.join(names) + ')'
        cur.expect_end()
        self.emit(f'class {name}{bases}:', at)
        self.class_bodies.append(self.depth + 1)
        self.block(['end class'], at)
        self.class_bodies.pop()

    def do_when(self, cur, at):
        if self.depth not in self.class_bodies:
            cur.fail('"when" can only be used directly inside a class.')
        if cur.accept_sequence('created'):
            parameters = ['this'] + self.parameter_list(cur)
            cur.expect_end()
            self.emit(f'def __init__({", ".join(parameters)}):', at)
        elif cur.accept_sequence('shown', 'as', 'text'):
            cur.expect_end()
            self.emit('def __str__(this):', at)
        else:
            cur.fail(f'I expected "created" or "shown as text" here{cur.found()}.')
        self.block(['end when'], at)

    # -- assignment: name = ..., a, b = ..., x[0] = ..., item 2 of x = ...

    def assignment_or_expression(self, cur, at):
        first, second = cur.peek(), cur.peek(1)
        is_operator = second is not None and second.kind == 'symbol' and second.value in ASSIGNMENT_OPERATORS
        if first.kind == 'word' and first.lower == 'item' and not is_operator:
            cur.i += 1
            position = parse_sum(cur)
            cur.expect_sequence('of')
            target = parse_postfix(cur)
            operator = cur.peek()
            if operator is None or operator.kind != 'symbol' or operator.value not in ASSIGNMENT_OPERATORS:
                cur.fail(f'I expected "=" here{cur.found()}.')
            cur.i += 1
            value = parse_expression(cur)
            cur.expect_end()
            if operator.value == '+=':
                value = f'_plus(_item({target}, {position}), {value})'
            elif operator.value not in ('=', '<-'):
                value = f'(_item({target}, {position}) {operator.value[0]} {value})'
            self.emit(f'_set_item({target}, {position}, {value})', at)
            return
        targets = [parse_postfix(cur)]
        while cur.accept_symbol(','):
            targets.append(parse_postfix(cur))
        operator = cur.peek()
        if operator is None:
            if len(targets) > 1 or re.fullmatch(r'[A-Za-z_]\w*', targets[0]) and first.kind == 'word' \
                    and cur.i == 1:
                if len(targets) == 1:
                    cur.fail(unknown_start(first.value))
                cur.fail('I expected "=" here but the line ended.')
            self.emit(targets[0], at)
            return
        if operator.kind != 'symbol' or operator.value not in ASSIGNMENT_OPERATORS:
            if len(targets) == 1 and cur.i == 1 and first.kind == 'word':
                cur.fail(unknown_start(first.value))
            cur.fail(f'I did not expect "{operator.value}" here.')
        cur.i += 1
        value = parse_value_list(cur)
        cur.expect_end()
        if operator.value == '+=' and len(targets) == 1:
            value = f'_plus_value({targets[0]}, {value})'  # so  message += 5  works when message is text
        self.emit(f'{", ".join(targets)} {"=" if operator.value == "<-" else operator.value} {value}', at)


STATEMENT_WORDS = {'print', 'output', 'display', 'ask', 'input', 'set', 'let', 'increase', 'decrease', 'add',
                   'subtract', 'multiply', 'divide', 'swap', 'remove', 'global', 'local',
                   'return', 'stop', 'skip', 'import', 'from', 'if', 'repeat', 'while', 'for', 'define', 'function',
                   'procedure', 'when', 'use'}


def suggest(word, candidates, cutoff=0.7):
    """The closest candidate to a misspelt word, or None."""
    matches = difflib.get_close_matches(word, sorted(set(candidates)), n=1, cutoff=cutoff)
    return matches[0] if matches else None


def unknown_start(word):
    message = f'I do not know how to start a line with "{word}".'
    close = suggest(word.lower(), STATEMENT_WORDS)
    return message + (f' Did you mean "{close}"?' if close else '')


def dotted_name(cur):
    name = cur.name()
    while cur.is_symbol('.'):
        cur.i += 1
        name += '.' + cur.name()
    return name


def hoist_definitions(out):
    """Moves imports, then functions and classes, to the top, so a program can use them before the
    line that defines them. Everything else keeps its order."""
    blocks = []
    for entry in out:
        text = entry[0]
        starts_new = text and not text[0].isspace() and not text.startswith(('elif ', 'else:'))
        if starts_new or not blocks:
            blocks.append([entry])
        else:
            blocks[-1].append(entry)

    def rank(block):
        first = block[0][0]
        if first.startswith(('import ', 'from ')) or re.match(r'[A-Za-z_]\w* = _use\(', first):
            return 0
        return 1 if first.startswith(('def ', 'class ')) else 2

    return [entry for block in sorted(blocks, key=rank) for entry in block]


def scope_nodes(node):
    """Everything inside `node` that belongs to the same scope: it looks inside ifs and loops,
    but not inside functions, classes or lambdas (it yields those, without going into them)."""
    for child in ast.iter_child_nodes(node):
        yield child
        if not isinstance(child, (ast.FunctionDef, ast.ClassDef, ast.Lambda)):
            yield from scope_nodes(child)


def own_nodes(function):
    """Every node in a function's own scope (not in functions or classes nested inside it)."""
    for statement in function.body:
        yield statement
        if not isinstance(statement, (ast.FunctionDef, ast.ClassDef, ast.Lambda)):
            yield from scope_nodes(statement)


def functions_in(node):
    """The functions defined under `node`, without crossing into another function."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef):
            yield child
        elif not isinstance(child, ast.Lambda):
            yield from functions_in(child)


def scope_note(node, kind):
    """Names from a 'global: a, b' or 'local: a' note statement, else an empty set."""
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        text = node.value.value
        if text.startswith(kind + ': '):
            return {name.strip() for name in text[len(kind) + 2:].split(',')}
    return set()


def declare_outer_variables(out):
    """Lets a function change a variable from outside it, as pseudocode does.

    Inside a function, assigning to a name that the main program also assigns changes that outside variable
    instead of making a new one. A function's own values (parameters), its loop counters and anything it
    declares with `local` stay private. `global name` makes a name outside-visible even when the main program
    never assigns it. A function nested in another function can change the outer function's variables too.
    """
    python = '\n'.join(text for text, _ in out) + '\n'
    try:
        tree = ast.parse(python)
    except SyntaxError:
        return out  # the problem is reported elsewhere
    module_names = {n.id for n in scope_nodes(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    insertions = []

    def visit(function, enclosing):
        arguments = function.args
        params = {a.arg for a in arguments.args + arguments.kwonlyargs + arguments.posonlyargs}
        stored, loops, local_notes, global_notes, nested = set(), set(), set(), set(), []
        for node in own_nodes(function):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                stored.add(node.id)
            elif isinstance(node, ast.For):
                loops.update(n.id for n in ast.walk(node.target) if isinstance(n, ast.Name))
            local_notes |= scope_note(node, 'local')
            global_notes |= scope_note(node, 'global')
        private = params | loops | local_notes
        outer_globals = {n for n in stored if n in module_names and n not in private and not n.startswith('_')}
        outer_globals |= global_notes - params
        enclosing_names = set().union(*enclosing) if enclosing else set()
        outer_locals = {n for n in stored if n not in outer_globals and n not in private
                        and n in enclosing_names and not n.startswith('_')}
        lines = []
        if outer_globals:
            lines.append('global ' + ', '.join(sorted(outer_globals)))
        if outer_locals:
            lines.append('nonlocal ' + ', '.join(sorted(outer_locals)))
        for name in sorted(local_notes - stored - params):
            lines.append(f'if False: {name} = None')  # makes the name private even if it is only ever read
        if lines:
            first = function.body[0].lineno - 1
            indent = out[first][0][:len(out[first][0]) - len(out[first][0].lstrip())]
            insertions.append((first, [(indent + text, out[function.lineno - 1][1]) for text in lines]))
        for inner in functions_in(function):
            visit(inner, enclosing + [params | stored | loops])

    for function in functions_in(tree):
        visit(function, [])
    result = list(out)
    for index, entries in sorted(insertions, reverse=True):
        result[index:index] = entries
    return result


def compile_speak(source, problems=None):
    """Turns Speak into Python. Returns (python, line_map).

    By default the first problem raises SpeakError. Give a list as `problems` to collect every
    problem found instead (used by the checker)."""
    lines = []
    for number, raw in enumerate(source.splitlines(), 1):
        text = raw.strip()
        if not text or re.match(r'note(\s|$)', text, re.I):
            continue
        try:
            tokens = tokenize(text, number)
        except SpeakError as error:
            if problems is None:
                raise
            problems.append(error)
            continue
        if not tokens:
            continue  # a line holding only a # comment
        indent = len(raw.expandtabs(4)) - len(raw.expandtabs(4).lstrip())
        lines.append(Line(tokens, number, indent))
    compiler = Compiler(lines, problems)
    compiler.run()
    out = declare_outer_variables(hoist_definitions(compiler.out))
    python = '\n'.join(text for text, _ in out) + '\n'
    return python, [number for _, number in out]


def undefined_names(tree, line_map):
    """Names used in the program that are never given a value anywhere in it (almost always a typo)."""
    stored, loads, star = set(), [], False
    in_text = set()  # names inside (brackets) in text may be missing on purpose, like "(yes or no)"
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda) and not node.args.args:
            in_text.update(id(inner) for inner in ast.walk(node.body) if isinstance(inner, ast.Name))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                loads.append(node)
            else:
                stored.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            stored.add(node.name)
        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            arguments = node.args
            stored.update(a.arg for a in arguments.args + arguments.kwonlyargs + arguments.posonlyargs)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == '*':
                    star = True
                stored.add((alias.asname or alias.name).split('.')[0])
    if star:
        return []  # "from x import *" can bring in any name
    known = stored | set(dir(builtins))
    problems, seen = [], set()
    for node in loads:
        name = node.id
        if name in known or name.startswith('_') or (name, node.lineno) in seen or id(node) in in_text:
            continue
        seen.add((name, node.lineno))
        close = suggest(name, stored)
        message = f'I do not know what "{name}" is. Did you forget to give it a value first?'
        if close:
            message += f' Did you mean "{close}"?'
        problems.append(SpeakError(message, line_map[node.lineno - 1]))
    return problems


def check_source(source):
    """Every problem that can be found without running the program: a list of (line, message)."""
    problems = []
    python, line_map = compile_speak(source, problems)
    try:
        tree = ast.parse(python)
    except SyntaxError as error:
        line = line_map[error.lineno - 1] if error.lineno and error.lineno <= len(line_map) else None
        problems.append(SpeakError('I could not understand this line.', line))
    else:
        problems.extend(undefined_names(tree, line_map))
    found, seen = [], set()
    for problem in sorted(problems, key=lambda e: (e.line or 0, str(e))):
        key = (problem.line, str(problem))
        if key not in seen:
            seen.add(key)
            found.append((problem.line or 1, str(problem)))
    return found


# ------------------------------------------------------------------ runtime

def _inner(value):
    return '"' + value + '"' if isinstance(value, str) else _show(value)


def _show(value):
    if value is None:
        return 'nothing'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return value
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(_inner(v) for v in value) + ']'
    return str(value)


def _fill(parts):
    """Joins the pieces of a text with (values): each piece is text, or (original, how to get the value)."""
    out = []
    for part in parts:
        if isinstance(part, str):
            out.append(part)
            continue
        original, get = part
        try:
            out.append(_show(get()))
        except NameError:  # no such variable (for example "(yes or no)"): keep the text as written
            out.append(original)
    return ''.join(out)


def _print(*values):
    print(' '.join(_show(v) for v in values))


def _use(name):
    """Loads the Speak version of a library (see speak_libraries), or the plain Python library."""
    import speak_libraries
    return speak_libraries.load(name)


# Values that "+" turns into text when the other side is text.
_TEXTUAL = (numbers.Number, list, tuple, dict, type(None))


def _plus(left, right):
    """left + right. If one side is text and the other a number (or true/false, nothing, a list),
    the other side is turned into text first, so "Total: " + total works."""
    if isinstance(left, str):
        if isinstance(right, _TEXTUAL):
            return left + _show(right)
    elif isinstance(right, str) and isinstance(left, _TEXTUAL):
        return _show(left) + right
    return left + right


def _plus_value(target, value):
    """What to add in `target += value`: the value as text when the target is text."""
    return _show(value) if isinstance(target, str) and isinstance(value, _TEXTUAL) else value


def _add(target, value):
    """add value to target: a list grows by one item; a number or text has the value added to it."""
    if isinstance(target, list):
        target.append(value)
        return target
    return _plus(target, value)


ASKED = {}  # variable name -> (Speak line, reply): lets errors say where a variable got its text


def _ask(prompt, name=None, line=None):
    """Asks a question. A reply that looks like a number comes back as a number."""
    shown = _show(prompt)
    reply = input(shown + ' ' if shown else '')
    text = reply.strip()
    if re.fullmatch(r'-?\d+', text):
        result = int(text)
    elif re.fullmatch(r'-?\d+\.\d+', text):
        result = float(text)
    else:
        result = reply
    if name:
        ASKED[name] = (line, result)
    return result


def _number(value):
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f'I cannot turn {_inner(value)} into a number.') from None


def _position(sequence, position):
    if isinstance(position, float) and position.is_integer():
        position = int(position)
    if not isinstance(position, int):
        raise TypeError('A position must be a whole number.')
    if position < 1 or position > len(sequence):
        raise IndexError(f'Position {position} does not exist. The length is {len(sequence)}, '
                         'and positions start at 1.')
    return position - 1


def _item(sequence, position):
    return sequence[_position(sequence, position)]


def _set_item(sequence, position, value):
    sequence[_position(sequence, position)] = value


def _remove_item(sequence, position):
    del sequence[_position(sequence, position)]


def _count(start, stop, step=1):
    if step == 0:
        raise ValueError('A counting loop cannot step by zero.')
    value = start
    while value <= stop if step > 0 else value >= stop:
        yield value
        value += step


KINDS = {'int': 'a number', 'float': 'a number', 'complex': 'a number', 'str': 'text', 'list': 'a list',
         'tuple': 'a tuple', 'dict': 'a dictionary', 'NoneType': 'nothing', 'bool': 'a true-or-false value',
         'ndarray': 'an array', 'set': 'a set'}
TEXT_HINT = (' One of them is text. If it came from "ask", the reply was not a number. '
             '"number version of" turns text such as "5" into a number.')


def kind_of(python_type_name):
    return KINDS.get(python_type_name, f'a {python_type_name}')


def explain_type_error(message, hint=''):
    """Plain English for the common TypeErrors; None if this one is not recognised."""
    m = re.search(r"'(<|>|<=|>=)' not supported between instances of '(\w+)' and '(\w+)'", message)
    if m:
        op, left, right = m.groups()
        advice = (' ' + hint if hint else '') + TEXT_HINT if 'str' in (left, right) else ''
        return f'I cannot compare {kind_of(left)} with {kind_of(right)} using "{op}".{advice}'
    m = re.search(r"unsupported operand type\(s\) for ([^:]+): '(\w+)' and '(\w+)'", message)
    if m:
        op, left, right = m.groups()
        advice = (' ' + hint if hint else '') + TEXT_HINT if 'str' in (left, right) else ''
        return f'I cannot use "{op.strip()}" with {kind_of(left)} and {kind_of(right)}.{advice}'
    m = re.search(r"bad operand type for unary (.): '(\w+)'", message)
    if m:
        return f'I cannot use "{m.group(1)}" in front of {kind_of(m.group(2))}.'
    m = re.search(r"(\S+)\(\) takes (\d+) positional arguments? but (\d+) (?:was|were) given", message)
    if m:
        name, wanted, given = m.group(1), int(m.group(2)), int(m.group(3))
        if '.' in name:  # a method: "this" is not something you pass
            name, wanted, given = name.split('.')[-1], wanted - 1, given - 1
        return f'"{name}" needs {wanted} value{"" if wanted == 1 else "s"} but was given {given}.'
    m = re.search(r"(\S+)\(\) missing (\d+) required positional arguments?: (.+)", message)
    if m:
        name = m.group(1).split('.')[-1]
        return f'"{name}" is missing a value for {m.group(3).replace(chr(39), chr(34))}.'
    m = re.search(r"'(\w+)' object is not (?:callable|subscriptable|iterable)", message)
    if m:
        what = {'callable': 'used like a function', 'subscriptable': 'used with [ ] or "item N of"',
                'iterable': 'looped over'}[re.search(r'callable|subscriptable|iterable', message).group()]
        kind = kind_of(m.group(1))
        return f'{kind[0].upper()}{kind[1:]} cannot be {what}.'
    return None


def asked_text_hint(python_line, frame):
    """If a variable on the failing line holds text that "ask" stored, say so."""
    if frame is None:
        return ''
    for name in dict.fromkeys(re.findall(r'[A-Za-z_]\w*', python_line)):
        if name in ASKED:
            line, reply = ASKED[name]
            value = frame.f_locals.get(name, frame.f_globals.get(name))
            if isinstance(value, str) and value == reply:
                return f'"{name}" holds the text "{value}" that "ask" stored on line {line}.'
    return ''


def explain_error(error, python, line_map):
    """Plain English for an error from a running program, with a hint about "ask" where it applies.
    Returns (message, Speak line, frame)."""
    line, frame = locate(error, line_map)
    hint = ''
    tb = error.__traceback__
    python_line_number = None
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == '<speak>':
            python_line_number = tb.tb_lineno
        tb = tb.tb_next
    if python_line_number:
        hint = asked_text_hint(python.split('\n')[python_line_number - 1], frame)
    names = list(frame.f_locals) + list(frame.f_globals) if frame is not None else []
    return explain(error, hint, names), line, frame


def did_you_mean(wrong, candidates):
    close = suggest(wrong, [c for c in candidates if not c.startswith('_')])
    return f' Did you mean "{close}"?' if close else ''


def explain(error, hint='', names=()):
    """Turn a Python error into a plain-English sentence. `names` are the variables that exist,
    used to suggest a spelling."""
    message = str(error)
    if isinstance(error, TypeError):
        plain = explain_type_error(message, hint)
        if plain:
            return plain
    if isinstance(error, AttributeError):
        owner_names = [n for n in dir(getattr(error, 'obj', None)) if not n.startswith('_')]
        m = re.search(r"'(\w+)' object has no attribute '(\w+)'", message)
        if m:
            owner = KINDS.get(m.group(1)) or f'a {m.group(1)}'
            return f'{owner[0].upper()}{owner[1:]} has no "{m.group(2)}".' + did_you_mean(m.group(2), owner_names)
        m = re.search(r"module '([\w.]+)' has no attribute '(\w+)'", message)
        if m:
            return (f'The library "{m.group(1).replace("speak_libraries.speak_", "")}" has no "{m.group(2)}".'
                    + did_you_mean(m.group(2), owner_names)
                    + ' For a Speak library, NAME.list_functions() shows what it offers.')
    if isinstance(error, KeyError):
        return f'The dictionary has no key {message}.'
    if isinstance(error, UnboundLocalError):
        m = re.search(r"'(\w+)'", message)
        name = m.group(1) if m else 'A name'
        return (f'"{name}" was used inside a function before it was given a value there. '
                f'Give it a value first, or write "global {name}" to use the one from outside.')
    if isinstance(error, NameError):
        m = re.search(r"'(\w+)'", message)
        wrong = getattr(error, 'name', None) or (m.group(1) if m else 'that')
        return (f'I do not know what "{wrong}" is. Did you forget to give it a value first?'
                + did_you_mean(wrong, names))
    if isinstance(error, ZeroDivisionError):
        return 'I cannot divide by zero.'
    if isinstance(error, ModuleNotFoundError):
        m = re.search(r"'([\w.]+)'", message)
        module = m.group(1) if m else 'that module'
        return f'I could not find the module "{module}". Install it with: pip install {module.split(".")[0]}'
    if isinstance(error, RecursionError):
        return 'A function called itself too many times.'
    if isinstance(error, TypeError) and 'concatenate' in message:
        return f'{message}. Use "text version of" to turn a value into text first.'
    if isinstance(error, (IndexError, ValueError)) and message.startswith(('I ', 'A ', 'Position')):
        return message
    if isinstance(error, IndexError):
        return 'That position does not exist in the list. Square brackets [ ] start at 0; "item N of" starts at 1.'
    return f'{type(error).__name__}: {message}'


def build_namespace(filename):
    return {
        '__name__': '__main__', '__file__': filename,
        '_math': math, '_random': random, '_show': _show, '_print': _print, '_ask': _ask,
        '_number': _number, '_use': _use, '_fill': _fill, '_add': _add, '_plus': _plus, '_plus_value': _plus_value, '_item': _item, '_set_item': _set_item, '_remove_item': _remove_item,
        '_count': _count,
    }


def compile_python(python, line_map):
    try:
        return compile(python, '<speak>', 'exec')
    except SyntaxError as error:
        line = line_map[error.lineno - 1] if error.lineno and error.lineno <= len(line_map) else None
        raise SpeakError('I could not understand this line.', line) from None


def compile_expression(text):
    """Turns one Speak expression into Python source (used by the debugger)."""
    cur = Cursor(tokenize(text.strip(), 0), 0)
    python = parse_value_list(cur)
    cur.expect_end()
    return python


def locate(error, line_map):
    """Finds the Speak line (and Python frame) where an error happened."""
    line = frame = None
    tb = error.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == '<speak>':
            line = line_map[tb.tb_lineno - 1]
            frame = tb.tb_frame
        tb = tb.tb_next
    return line, frame


def run_source(source, filename='<speak>'):
    python, line_map = compile_speak(source)
    code = compile_python(python, line_map)
    try:
        exec(code, build_namespace(filename))
    except (SystemExit, KeyboardInterrupt, SpeakError):
        raise
    except Exception as error:  # noqa: BLE001 - reported in plain English
        message, line, _ = explain_error(error, python, line_map)
        raise SpeakError(message, line) from None


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            pass
    if len(argv) >= 2 and argv[1] == '--check-json':
        # Used by the VS Code extension: reads a program on standard input, prints its problems as JSON.
        source = sys.stdin.buffer.read().decode('utf-8')
        print(json.dumps([{'line': line, 'message': message} for line, message in check_source(source)]))
        return 0
    if len(argv) < 2:
        print('Usage: python speak.py <file.speak>', file=sys.stderr)
        return 1
    path = argv[1]
    try:
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
    except OSError:
        print(f'I could not open "{path}".', file=sys.stderr)
        return 1
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    try:
        run_source(source, os.path.abspath(path))
    except SpeakError as error:
        where = f'Line {error.line}: ' if error.line else ''
        print(f'\nSpeak problem in {os.path.basename(path)}\n{where}{error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
