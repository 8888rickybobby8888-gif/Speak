"""Tests for the Speak libraries. Run: python -m unittest discover tests"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
os.environ.setdefault('MPLBACKEND', 'Agg')

import speak  # noqa: E402


def run(source):
    """Runs Speak source and returns what it printed."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        speak.run_source(source)
    return out.getvalue()


def has(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


class UseStatement(unittest.TestCase):
    def test_use_gives_the_speak_version(self):
        self.assertEqual(run('use math\nprint math.square_root(16)\n'), '4\n')

    def test_use_with_alias(self):
        self.assertEqual(run('use math as sums\nprint sums.hypotenuse(3, 4)\n'), '5\n')

    def test_several_libraries_on_one_line(self):
        self.assertEqual(run('use math, random\nprint math.is_prime(7), random.whole_number(2, 2)\n'), 'true 2\n')

    def test_plain_python_library_still_works_with_use(self):
        self.assertEqual(run('use json\nprint json.dumps([1])\n'), '[1]\n')

    def test_unknown_library_explains_itself(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('use nonsense_library\n')
        self.assertIn('I do not know a library called "nonsense_library"', str(caught.exception))
        self.assertEqual(caught.exception.line, 1)

    def test_list_functions_prints_the_library(self):
        text = run('use random\nrandom.list_functions()\n')
        self.assertIn('pick_one(items)', text)
        self.assertIn('One random item from a list.', text)

    def test_raw_library_is_available(self):
        self.assertEqual(run('use math\nprint math.raw.floor(2.7)\n'), '2\n')


class SimpleLibraries(unittest.TestCase):
    def test_math(self):
        text = run('use math\nprint math.sine(90), math.round_up(2.1), math.greatest_common_divisor(12, 18), '
                   'math.average([1, 2, 3])\n')
        self.assertEqual(text, '1 3 6 2\n')

    def test_random_is_in_range(self):
        self.assertEqual(run('use random\nprint random.roll_dice(1), random.pick_one(["a"])\n'), '1 a\n')

    def test_random_errors_in_plain_english(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('use random\nprint random.pick_one([])\n')
        self.assertIn('I cannot pick from an empty list.', str(caught.exception))

    def test_time(self):
        text = run('use time\nt = time.start_timer()\ntime.wait(0.01)\nprint time.seconds_since(t) > 0.005, '
                   'length of time.today()\n')
        self.assertEqual(text, 'true 10\n')


@unittest.skipUnless(has('numpy'), 'numpy is not installed')
class NumpyLibrary(unittest.TestCase):
    def test_statistics(self):
        text = run('use numpy\nn = numpy.array([2, 4, 4, 4, 5, 5, 7, 9])\n'
                   'print numpy.mean(n), numpy.standard_deviation(n), numpy.median(n), numpy.total(n)\n')
        self.assertEqual(text, '5 2 4.5 40\n')

    def test_positions_count_from_one(self):
        text = run('use numpy\nn = numpy.array([5, 9, 1])\n'
                   'print numpy.position_of_largest(n), item numpy.position_of_smallest(n) of n\n')
        self.assertEqual(text, '2 1\n')

    def test_numbers_from_to_includes_the_end(self):
        self.assertEqual(run('use numpy\nprint numpy.numbers_from_to(1, 10, 3)\n'), '[ 1  4  7 10]\n')
        self.assertEqual(run('use numpy\nprint numpy.numbers_from_to(5, 1, -2)\n'), '[5 3 1]\n')

    def test_grids(self):
        text = run('use numpy\ng = numpy.reshape(numpy.numbers_from_to(1, 6), 2, 3)\n'
                   'print numpy.rows_of(g), numpy.columns_of(g), numpy.column_of(g, 2), numpy.row_of(g, 1)\n')
        self.assertEqual(text, '2 3 [2 5] [1 2 3]\n')

    def test_maths_on_every_item(self):
        self.assertEqual(run('use numpy\nprint numpy.square_root(numpy.array([4, 9])), '
                             'numpy.round_to(numpy.array([1.26, 2.34]), 1)\n'), '[2. 3.] [1.3 2.3]\n')

    def test_list_of_gives_a_normal_list(self):
        self.assertEqual(run('use numpy\nprint numpy.list_of(numpy.array([1, 2]))\n'), '[1, 2]\n')


@unittest.skipUnless(has('matplotlib'), 'matplotlib is not installed')
class MatplotlibLibrary(unittest.TestCase):
    def test_saves_a_chart(self):
        path = os.path.join(tempfile.mkdtemp(), 'chart.png').replace('\\', '/')
        run(f'use matplotlib\nmatplotlib.new_chart(4, 3)\nmatplotlib.line_chart([1, 2, 3], [1, 4, 9], "squares")\n'
            f'matplotlib.bar_chart(["a", "b"], [2, 3])\nmatplotlib.title("T")\nmatplotlib.legend()\n'
            f'matplotlib.save_chart("{path}")\nmatplotlib.close_chart()\n')
        self.assertTrue(os.path.getsize(path) > 500)


@unittest.skipUnless(has('pandas'), 'pandas is not installed')
class PandasLibrary(unittest.TestCase):
    def test_tables(self):
        text = run('use pandas\n'
                   't = pandas.make_table({"name": ["Ada", "Alan", "Grace"], "age": [36, 41, 50]})\n'
                   'print pandas.number_of_rows(t), pandas.average_of_column(t, "age"), pandas.column_names(t)\n'
                   'print pandas.number_of_rows(pandas.rows_above(t, "age", 40))\n'
                   'print pandas.sort_table(t, "age", true).iloc[0]["name"]\n')
        self.assertEqual(text, '3 42.333333333333336 ["name", "age"]\n2\nGrace\n')

    def test_missing_column_is_explained(self):
        with self.assertRaises(speak.SpeakError) as caught:
            run('use pandas\nt = pandas.make_table({"a": [1]})\nprint pandas.column_of(t, "b")\n')
        self.assertIn('The table has no column called "b"', str(caught.exception))


@unittest.skipUnless(has('micromelon'), 'micromelon is not installed')
class MicromelonLibrary(unittest.TestCase):
    """The rover is replaced by mocks, so these check what would be sent to it."""

    def setUp(self):
        import micromelon
        from speak_libraries import speak_micromelon as mm
        self.mm, self.micromelon = mm, micromelon
        controller = mock.MagicMock()
        patcher = mock.patch.object(micromelon, 'RoverController', return_value=controller)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.controller = controller
        mm.connect_to_simulator()
        self.addCleanup(setattr, mm, '_controller', None)

    def patched(self, module, name):
        patcher = mock.patch.object(module, name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_connecting_starts_the_rover(self):
        self.controller.connectIP.assert_called_once_with('127.0.0.1', 9000)
        self.controller.startRover.assert_called_once()
        self.assertTrue(self.mm._controller is self.controller)

    def test_disconnect(self):
        self.mm.disconnect()
        self.controller.stopRover.assert_called_once()
        self.controller.disconnect.assert_called_once()
        self.assertFalse(self.mm.is_connected())

    def test_driving(self):
        write = self.patched(self.micromelon.Motors, 'write')
        move = self.patched(self.micromelon.Motors, 'moveDistance')
        turn = self.patched(self.micromelon.Motors, 'turnDegrees')
        self.mm.drive_forward(10)
        write.assert_called_with(10, None, 0)
        self.mm.drive_backward(10, seconds=2)
        write.assert_called_with(-10, None, 2)
        self.mm.stop_moving()
        write.assert_called_with(0, 0)
        self.mm.drive_forward_distance(30)
        move.assert_called_with(30, 15)
        self.mm.drive_backward_distance(30, 20)
        move.assert_called_with(-30, 20)
        self.mm.turn_left(90)
        turn.assert_called_with(-90, 15)
        self.mm.turn_right(45, 10)
        turn.assert_called_with(45, 10)

    def test_sensors(self):
        self.patched(self.micromelon.Ultrasonic, 'read').return_value = 42
        self.patched(self.micromelon.IR, 'readLeft').return_value = 7.5
        self.patched(self.micromelon.Battery, 'readPercentage').return_value = 80
        sees = self.patched(self.micromelon.Colour, 'sensorSees')
        sees.return_value = True
        self.assertEqual(self.mm.distance_ahead(), 42)
        self.assertEqual(self.mm.left_distance(), 7.5)
        self.assertEqual(self.mm.battery_percentage(), 80)
        self.assertTrue(self.mm.sees_colour('red', 'left', 10))
        sees.assert_called_with([255, 0, 34], 0, 10)

    def test_lights_and_colours(self):
        write_all = self.patched(self.micromelon.LEDs, 'writeAll')
        write = self.patched(self.micromelon.LEDs, 'write')
        self.mm.set_all_lights('blue')
        write_all.assert_called_with(list(self.micromelon.COLOURS.BLUE.value))
        self.mm.set_light(2, [1, 2, 3])
        write.assert_called_with(2, [1, 2, 3])
        with self.assertRaises(ValueError) as caught:
            self.mm.colour('not a colour')
        self.assertIn('I do not know a colour called "not a colour"', str(caught.exception))

    def test_notes(self):
        play = self.patched(self.micromelon.Sounds, 'playNote')
        self.mm.play_note('C4')
        play.assert_called_with(self.micromelon.NOTES.C4.value, None)
        self.mm.play_note('F#5', 1)
        play.assert_called_with(self.micromelon.NOTES.FsGb5.value, 1)
        self.mm.play_note('Bb3')
        play.assert_called_with(self.micromelon.NOTES.AsBb3.value, None)
        self.mm.play_note(440)
        play.assert_called_with(440, None)

    def test_servos_and_imu_axes(self):
        left = self.patched(self.micromelon.Servos, 'left')
        accel = self.patched(self.micromelon.IMU, 'readAccel')
        self.mm.move_left_servo(30)
        left.assert_called_with(30)
        self.mm.acceleration('z')
        accel.assert_called_with(2)
        self.mm.acceleration()
        accel.assert_called_with(None)

    def test_not_connected_is_explained(self):
        self.mm.disconnect()
        with self.assertRaises(ValueError) as caught:
            self.mm.drive_forward()
        self.assertIn('I am not connected to a robot yet', str(caught.exception))

    def test_speak_program_drives_the_rover(self):
        write = self.patched(self.micromelon.Motors, 'write')
        self.patched(self.micromelon.Ultrasonic, 'read').return_value = 12
        run('use micromelon\nif micromelon.distance_ahead() < 20 then\n  micromelon.stop_moving()\n')
        write.assert_called_with(0, 0)


if __name__ == '__main__':
    unittest.main()
