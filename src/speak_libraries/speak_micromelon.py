"""Micromelon rover control in plain English (needs: pip install micromelon).

Typical use, with the Micromelon Robot Simulator running:
    use micromelon
    micromelon.connect_to_simulator()
    micromelon.drive_forward_distance(30)
    micromelon.turn_right(90)
    print micromelon.distance_ahead()
    micromelon.disconnect()

Speeds are in centimetres per second (-30 to 30), distances in centimetres, angles in degrees.
Colours can be a name such as "red" or a list of three numbers [red, green, blue] from 0 to 255.
Notes can be a name such as "C4" or "F#5" (or "Bb3"), or a frequency in hertz.
Sensors can be "left", "middle" or "right"; axes can be "x", "y" or "z".
The original library is available as `raw`.
"""
import time as _time

import micromelon as _micromelon

raw = _micromelon
_controller = None


def _connected():
    if _controller is None:
        raise ValueError('I am not connected to a robot yet. Use connect_to_simulator(), '
                         'connect_by_bluetooth(number) or connect_by_serial() first.')


def _colour(value):
    if isinstance(value, str):
        name = value.strip().upper().replace(' ', '_')
        try:
            return list(_micromelon.COLOURS[name].value)
        except KeyError:
            known = ', '.join(sorted(c.name.lower() for c in _micromelon.COLOURS))
            raise ValueError(f'I do not know a colour called "{value}". Known colours: {known}.') from None
    if len(value) != 3:
        raise ValueError('A colour is a name like "red" or a list of three numbers [red, green, blue].')
    return list(value)


def _frequency(value):
    if not isinstance(value, str):
        return value
    text = value.strip().replace('#', 's')
    letters = 'CDEFGAB'
    if len(text) < 2 or text[0].upper() not in letters:
        raise ValueError(f'I do not know a note called "{value}". Try something like "C4", "F#5" or "Bb3".')
    letter, rest = text[0].upper(), text[1:]
    name = letter + rest
    if rest[0] == 's':
        name = letter + 's' + letters[(letters.index(letter) + 1) % 7] + 'b' + rest[1:]
    elif rest[0] == 'b':
        name = letters[(letters.index(letter) - 1) % 7] + 's' + letter + 'b' + rest[1:]
    try:
        return _micromelon.NOTES[name].value
    except KeyError:
        raise ValueError(f'I do not know a note called "{value}". Try something like "C4", "F#5" or "Bb3".') from None


def _sensor(value):
    names = {'left': 0, 'middle': 1, 'right': 2}
    if isinstance(value, str):
        if value.lower() not in names:
            raise ValueError('A sensor is "left", "middle" or "right".')
        return names[value.lower()]
    return value


def _axis(value):
    if value is None:
        return None
    names = {'x': 0, 'y': 1, 'z': 2}
    if isinstance(value, str):
        if value.lower() not in names:
            raise ValueError('An axis is "x", "y" or "z".')
        return names[value.lower()]
    return value


# ---- connecting

def _connect(connect, what, advice):
    global _controller
    controller = _micromelon.RoverController()
    try:
        connect(controller)
        controller.startRover()
    except Exception as error:  # noqa: BLE001 - explained in plain English
        raise ValueError(f'I could not connect to {what}. {advice} ({type(error).__name__}: {error})') from None
    _controller = controller


def connect_to_simulator(address='127.0.0.1', port=9000):
    """Connects to the Micromelon Robot Simulator (or any rover on the network) and starts it."""
    _connect(lambda c: c.connectIP(address, port), f'the rover at {address}:{port}',
             'Is the Micromelon Robot Simulator running, with a robot added?')


def connect_by_bluetooth(robot_number):
    """Connects to a real rover over Bluetooth using the number on its label, and starts it."""
    _connect(lambda c: c.connectBLE(robot_number), f'rover number {robot_number}',
             'Is it switched on, close by, and not connected to anything else?')


def connect_by_serial(port='/dev/ttyS0'):
    """Connects to a rover attached to a Raspberry Pi serial port, and starts it."""
    _connect(lambda c: c.connectSerial(port), f'the rover on serial port {port}',
             'Is it plugged in and switched on?')


def disconnect():
    """Stops the rover and disconnects from it."""
    global _controller
    if _controller is not None:
        _controller.stopRover()
        _controller.disconnect()
        _controller = None


def is_connected():
    """True if the program is connected to a rover."""
    return _controller is not None and _controller.isConnected()


# ---- driving

def drive(left_speed, right_speed=None, seconds=0):
    """Sets the speed of the left and right wheels. With seconds, drives that long then stops."""
    _connected()
    _micromelon.Motors.write(left_speed, right_speed, seconds)


def drive_forward(speed=15, seconds=0):
    """Drives forward at this speed. With seconds, drives that long then stops."""
    _connected()
    _micromelon.Motors.write(abs(speed), None, seconds)


def drive_backward(speed=15, seconds=0):
    """Drives backward at this speed. With seconds, drives that long then stops."""
    _connected()
    _micromelon.Motors.write(-abs(speed), None, seconds)


def drive_forward_distance(centimetres, speed=15):
    """Drives forward this far, then stops. The program waits until it arrives."""
    _connected()
    _micromelon.Motors.moveDistance(abs(centimetres), speed)


def drive_backward_distance(centimetres, speed=15):
    """Drives backward this far, then stops. The program waits until it arrives."""
    _connected()
    _micromelon.Motors.moveDistance(-abs(centimetres), speed)


def drive_each_side_distance(left_centimetres, left_speed, right_centimetres, right_speed):
    """Drives each side a different distance at a different speed, which makes a curve."""
    _connected()
    _micromelon.Motors.moveDistance(left_centimetres, left_speed, right_centimetres, right_speed)


def turn_left(degrees, speed=15):
    """Turns on the spot to the left by this many degrees."""
    _connected()
    _micromelon.Motors.turnDegrees(-abs(degrees), speed)


def turn_right(degrees, speed=15):
    """Turns on the spot to the right by this many degrees."""
    _connected()
    _micromelon.Motors.turnDegrees(abs(degrees), speed)


def stop_moving():
    """Stops both wheels."""
    _connected()
    _micromelon.Motors.write(0, 0)


# ---- sensors

def distance_ahead():
    """The distance in centimetres to the nearest thing in front, from the ultrasonic sensor."""
    _connected()
    return _micromelon.Ultrasonic.read()


def left_distance():
    """The distance in centimetres measured by the left infrared sensor."""
    _connected()
    return _micromelon.IR.readLeft()


def right_distance():
    """The distance in centimetres measured by the right infrared sensor."""
    _connected()
    return _micromelon.IR.readRight()


def both_distances():
    """The left and right infrared distances as a list [left, right]."""
    _connected()
    return _micromelon.IR.readAll()


def colour_hue(sensor='middle'):
    """The hue (0 to 359) that a colour sensor sees."""
    _connected()
    return _micromelon.Colour.readSensor(_micromelon.CS.HUE, _sensor(sensor))


def colour_values(sensor='middle'):
    """Everything a colour sensor reads: its colour amounts and brightness."""
    _connected()
    return _micromelon.Colour.readSensor(_micromelon.CS.ALL, _sensor(sensor))


def sees_colour(colour, sensor='middle', tolerance=20):
    """True if a colour sensor sees this colour (a name or [red, green, blue])."""
    _connected()
    return _micromelon.Colour.sensorSees(_colour(colour), _sensor(sensor), tolerance)


def battery_percentage():
    """How full the battery is, as a percentage."""
    _connected()
    return _micromelon.Battery.readPercentage()


def battery_voltage():
    """The battery voltage in volts."""
    _connected()
    return _micromelon.Battery.readVoltage()


def is_upside_down():
    """True if the rover has flipped over."""
    _connected()
    return _micromelon.IMU.isFlipped()


def is_upright():
    """True if the rover is the right way up."""
    _connected()
    return _micromelon.IMU.isRighted()


def acceleration(axis=None):
    """How hard the rover is accelerating, in g. Give an axis ("x", "y" or "z") or get all three."""
    _connected()
    return _micromelon.IMU.readAccel(_axis(axis))


def turning_speed(axis=None):
    """How fast the rover is turning, in degrees per second. Give an axis or get all three."""
    _connected()
    return _micromelon.IMU.readGyro(_axis(axis))


def degrees_turned(axis=None):
    """About how many degrees the rover has turned since it started. Give an axis or get all three."""
    _connected()
    return _micromelon.IMU.readGyroAccum(_axis(axis))


# ---- lights, sounds, screen, servos

def colour(name):
    """The [red, green, blue] numbers for a named colour, such as "orange"."""
    return _colour(name)


def colour_from_hex(code):
    """The [red, green, blue] numbers for a hex code like "#FF8800"."""
    return _micromelon.Colour.hexToRgb(code)


def set_light(number, colour):
    """Sets one of the four lights (numbered 1 to 4) to a colour name or [red, green, blue]."""
    _connected()
    _micromelon.LEDs.write(number, _colour(colour))


def set_all_lights(first_colour, second_colour=None, third_colour=None, fourth_colour=None):
    """Sets all four lights to one colour, or give four colours, one for each light."""
    _connected()
    colours = [first_colour, second_colour, third_colour, fourth_colour]
    given = [_colour(c) for c in colours if c is not None]
    _micromelon.LEDs.writeAll(*given)


def lights_off():
    """Turns all the lights off."""
    _connected()
    _micromelon.LEDs.off()


def play_note(note, seconds=None):
    """Plays a note (a name like "C4" or a frequency in hertz). With seconds, waits that long."""
    _connected()
    _micromelon.Sounds.playNote(_frequency(note), seconds)


def play_tune(name):
    """Plays a built-in tune: "up" or "down"."""
    _connected()
    try:
        tune = _micromelon.TUNES[name.strip().upper()]
    except (KeyError, AttributeError):
        raise ValueError('I know the tunes "up" and "down".') from None
    _micromelon.Sounds.play(tune)


def silence():
    """Stops any sound."""
    _connected()
    _micromelon.Sounds.off()


def show_on_screen(text, label=None):
    """Shows text on the rover's screen (up to 15 letters)."""
    _connected()
    _micromelon.Robot.display(text, label)


def robot_name():
    """The name of the connected rover."""
    _connected()
    return _micromelon.Robot.getName()


def set_robot_name(name):
    """Gives the connected rover a new name."""
    _connected()
    _micromelon.Robot.setName(name)


def move_left_servo(degrees):
    """Turns the left servo to an angle from -90 to 90 degrees."""
    _connected()
    _micromelon.Servos.left(degrees)


def move_right_servo(degrees):
    """Turns the right servo to an angle from -90 to 90 degrees."""
    _connected()
    _micromelon.Servos.right(degrees)


def move_both_servos(left_degrees, right_degrees):
    """Turns both servos to angles from -90 to 90 degrees."""
    _connected()
    _micromelon.Servos.setBoth(left_degrees, right_degrees)


def servo_angles():
    """The current angles of the servos as a list [left, right]."""
    _connected()
    return _micromelon.Servos.read()


# ---- helpers

def wait(seconds):
    """Pauses the program for this many seconds."""
    _time.sleep(seconds)


def keep_between(number, lowest, highest):
    """The number, but no lower than lowest and no higher than highest."""
    return _micromelon.Math.constrain(number, lowest, highest)


def scale_between(number, from_lowest, from_highest, to_lowest, to_highest):
    """Converts a number from one range to another, for example a sensor reading to a speed."""
    return _micromelon.Math.scale(number, from_lowest, from_highest, to_lowest, to_highest)
