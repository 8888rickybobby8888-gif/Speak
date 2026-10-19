"""Tests for the whole-file checker used by the VS Code Problems panel. Run: python -m unittest discover tests"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import speak  # noqa: E402


def problems(source):
    return speak.check_source(source)


class Check(unittest.TestCase):
    def test_clean_program_has_no_problems(self):
        self.assertEqual(problems('x = 1\nprint "x is (x)"\n'), [])

    def test_every_example_is_clean(self):
        folder = os.path.join(HERE, '..', 'examples')
        for name in sorted(os.listdir(folder)):
            if name.endswith('.speak'):
                with self.subTest(name):
                    with open(os.path.join(folder, name), encoding='utf-8') as handle:
                        self.assertEqual(problems(handle.read()), [])

    def test_reports_every_mistake_not_just_the_first(self):
        found = problems('prnt "a"\nx = 1\nprint "unclosed\ny = (1 + 2\nz = nothing_here + 1\n')
        lines = [line for line, _ in found]
        self.assertEqual(lines, [1, 3, 4, 5])

    def test_misspelt_command_has_a_suggestion(self):
        (line, message), = problems('prnt "a"\n')
        self.assertEqual(line, 1)
        self.assertIn('Did you mean "print"?', message)

    def test_unknown_name_found_without_running(self):
        (line, message), = problems('x = 1\nprint y\n')
        self.assertEqual(line, 2)
        self.assertIn('I do not know what "y" is', message)

    def test_misspelt_name_has_a_suggestion(self):
        (_, message), = problems('score = 1\nprint scroe\n')
        self.assertIn('Did you mean "score"?', message)

    def test_names_in_text_brackets_are_not_flagged(self):
        self.assertEqual(problems('print "Done? (yes or no)"\nask "Ok? (y or n)" store as a\n'), [])

    def test_function_used_before_definition_is_fine(self):
        self.assertEqual(problems('f()\nfunction f()\n  print 1\nendfunction\n'), [])

    def test_parameters_loop_variables_imports_and_library_names_are_known(self):
        source = ('use math\nimport os\nfrom math import sqrt as root\n'
                  'function f(a, b)\n  return a + b + root(4)\nendfunction\n'
                  'for n from 1 to 2\n  print f(n, math.pi)\nend for\n'
                  'for each c in "ab"\n  print c\n'
                  'define class T\n  when created with v\n    this.v = v\n  end when\nend class\n'
                  'print os.sep, T(1).v\n')
        self.assertEqual(problems(source), [])

    def test_star_import_switches_name_checking_off(self):
        self.assertEqual(problems('from math import *\nprint sqrt(4), anything\n'), [])

    def test_unclosed_block_is_reported_once_on_its_opening_line(self):
        found = problems('while 1 = 1\nprint 1\n')
        self.assertEqual([line for line, _ in found], [1])
        self.assertIn('end while', found[0][1])

    def test_a_bad_header_does_not_flood_with_knock_on_errors(self):
        found = problems('if 1 = = 2 then\n  print "a"\n  print "b"\nend if\nprint "c"\n')
        self.assertEqual([line for line, _ in found], [1])

    def test_problems_inside_a_function_are_found(self):
        found = problems('function f()\n  prnt "x"\nendfunction\n')
        self.assertEqual([line for line, _ in found], [2])

    def test_problems_come_back_sorted_and_without_duplicates(self):
        found = problems('print a\nprint a\nprint b\n')
        self.assertEqual([line for line, _ in found], [1, 2, 3])

    def test_command_line_check_prints_json(self):
        result = subprocess.run([sys.executable, os.path.join(HERE, '..', 'src', 'speak.py'), '--check-json'],
                                input='prnt "x"\nprint y\n'.encode('utf-8'), capture_output=True, check=True)
        data = json.loads(result.stdout.decode('utf-8'))
        self.assertEqual([d['line'] for d in data], [1, 2])
        self.assertTrue(all('message' in d for d in data))

    def test_command_line_check_handles_unicode_and_empty_input(self):
        run = lambda text: json.loads(subprocess.run(  # noqa: E731
            [sys.executable, os.path.join(HERE, '..', 'src', 'speak.py'), '--check-json'],
            input=text.encode('utf-8'), capture_output=True, check=True).stdout.decode('utf-8'))
        self.assertEqual(run(''), [])
        self.assertEqual(run('x \u2190 1\nprint "caf\u00e9 (x)"\n'), [])


if __name__ == '__main__':
    unittest.main()
