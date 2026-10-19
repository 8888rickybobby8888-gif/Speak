"""Tests for the Speak language itself. Run: python -m unittest discover tests"""
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import speak  # noqa: E402


def run(source, answers=()):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), mock.patch('builtins.input', side_effect=list(answers)):
        speak.run_source(source)
    return out.getvalue()


class Blocks(unittest.TestCase):
    def test_end_lines_are_optional_when_indented(self):
        source = 'if 1 = 2 then\n  print "a"\notherwise\n  print "b"\nprint "after"\n'
        self.assertEqual(run(source), 'b\nafter\n')

    def test_else_is_accepted(self):
        self.assertEqual(run('if 1 = 1 then\n  print "yes"\nelse\n  print "no"\n'), 'yes\n')

    def test_else_if_is_accepted(self):
        self.assertEqual(run('x = 5\nif x < 3 then\n  print "low"\nelse if x < 9 then\n  print "mid"\n'), 'mid\n')

    def test_unindented_if_without_end_takes_one_statement(self):
        self.assertEqual(run('if 1 = 1 then\nprint 1\nprint 2\n'), '1\n2\n')
        self.assertEqual(run('if 1 = 2 then\nprint 1\nprint 2\n'), '2\n')

    def test_unindented_while_still_needs_end(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('while 1 = 1\nprint 1\n')
        self.assertIn('Add "end while"', str(caught.exception))
        self.assertEqual(caught.exception.line, 1)

    def test_explicit_end_still_works(self):
        self.assertEqual(run('repeat 2 times\nprint "x"\nend repeat\nprint "y"\n'), 'x\nx\ny\n')

    def test_dedent_closes_a_function(self):
        source = 'define function f\n  print "inside"\nprint "outside"\nf()\n'
        self.assertEqual(run(source), 'outside\ninside\n')


class Ask(unittest.TestCase):
    def test_numbers_come_back_as_numbers(self):
        source = 'ask "q" store as a\nif a = 20 then\n  print "correct"\nelse\n  print "incorrect"\n'
        self.assertEqual(run(source, ['20']), 'correct\n')

    def test_other_replies_stay_text(self):
        self.assertEqual(run('ask "q" store as a\nprint a + "!"\n', ['hi']), 'hi!\n')

    def test_decimals(self):
        self.assertEqual(run('ask "q" store as a\nprint a * 2\n', ['2.5']), '5\n')


class AskPrompt(unittest.TestCase):
    def test_question_gets_values_filled_in(self):
        asked = []
        source = 'name = "Ada"\nask "Hello (name), how old are you?" store as age\nprint "age (age)"\n'
        out = io.StringIO()

        def fake_input(prompt):
            asked.append(prompt)
            return '36'
        with contextlib.redirect_stdout(out), mock.patch('builtins.input', fake_input):
            speak.run_source(source)
        self.assertEqual(asked, ['Hello Ada, how old are you? '])
        self.assertEqual(out.getvalue(), 'age 36\n')

    def test_input_prompt_gets_values_filled_in(self):
        asked = []
        out = io.StringIO()

        def fake_input(prompt):
            asked.append(prompt)
            return 'x'
        with contextlib.redirect_stdout(out), mock.patch('builtins.input', fake_input):
            speak.run_source('n = 2\ninput "Item (n)?" store as reply\n')
        self.assertEqual(asked, ['Item 2? '])

    def test_brackets_that_are_not_values_stay(self):
        asked = []

        def fake_input(prompt):
            asked.append(prompt)
            return 'yes'
        with contextlib.redirect_stdout(io.StringIO()), mock.patch('builtins.input', fake_input):
            speak.run_source('ask "Done? (yes or no)" store as reply\n')
        self.assertEqual(asked, ['Done? (yes or no) '])


class Classes(unittest.TestCase):
    SOURCE = (
        'define class Animal\n  when created with name\n    this.name = name\n  end when\n'
        '  define function speak\n    return this.name + " makes a sound"\n  end function\n'
        '  when shown as text\n    return "Animal " + this.name\n  end when\nend class\n'
        'define class Dog extends Animal\n  when created with name\n    call parent with name\n  end when\n'
        '  define function speak\n    return parent.speak() + " (woof)"\n  end function\nend class\n'
    )

    def test_inheritance_parent_and_text_form(self):
        text = run(self.SOURCE + 'pet = create Dog with "Rex"\nprint pet.speak()\nprint pet\n')
        self.assertEqual(text, 'Rex makes a sound (woof)\nAnimal Rex\n')


class Errors(unittest.TestCase):
    def test_unknown_name_is_explained_with_the_line(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('x = 1\nprint y\n')
        self.assertIn('I do not know what "y" is', str(caught.exception))
        self.assertEqual(caught.exception.line, 2)

    def test_item_positions_count_from_one(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('items = [1, 2]\nprint item 3 of items\n')
        self.assertIn('Position 3 does not exist', str(caught.exception))


class Examples(unittest.TestCase):
    """Every example that needs no input, hardware or extra packages should run."""

    def test_examples_compile(self):
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples')
        for name in sorted(os.listdir(folder)):
            if name.endswith('.speak'):
                with self.subTest(name):
                    with open(os.path.join(folder, name), encoding='utf-8') as handle:
                        speak.compile_speak(handle.read())


if __name__ == '__main__':
    unittest.main()
