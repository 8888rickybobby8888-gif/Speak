"""Maths in plain English. Angles are in degrees.

Constants: pi, e
"""
import math as _math

raw = _math
pi = _math.pi
e = _math.e


def square_root(number):
    """The square root of a number."""
    return _math.sqrt(number)


def power(number, exponent):
    """The number multiplied by itself exponent times."""
    return _math.pow(number, exponent)


def absolute(number):
    """The number without its minus sign."""
    return abs(number)


def round_down(number):
    """The whole number at or just below the number."""
    return _math.floor(number)


def round_up(number):
    """The whole number at or just above the number."""
    return _math.ceil(number)


def round_to(number, places=0):
    """The number rounded to this many decimal places."""
    return round(number, places)


def sine(degrees):
    """The sine of an angle in degrees."""
    return _math.sin(_math.radians(degrees))


def cosine(degrees):
    """The cosine of an angle in degrees."""
    return _math.cos(_math.radians(degrees))


def tangent(degrees):
    """The tangent of an angle in degrees."""
    return _math.tan(_math.radians(degrees))


def degrees_to_radians(degrees):
    """Converts an angle from degrees to radians."""
    return _math.radians(degrees)


def radians_to_degrees(radians):
    """Converts an angle from radians to degrees."""
    return _math.degrees(radians)


def logarithm(number, base=10):
    """The logarithm of a number (base 10 unless you give another base)."""
    return _math.log(number, base)


def natural_logarithm(number):
    """The logarithm of a number to the base e."""
    return _math.log(number)


def factorial(number):
    """The product of every whole number from 1 up to the number."""
    return _math.factorial(number)


def greatest_common_divisor(first, second):
    """The largest whole number that divides both numbers exactly."""
    return _math.gcd(first, second)


def hypotenuse(first_side, second_side):
    """The long side of a right-angled triangle with these two shorter sides."""
    return _math.hypot(first_side, second_side)


def is_prime(number):
    """True if the number is a prime number."""
    if number < 2 or number != int(number):
        return False
    number = int(number)
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


def average(numbers):
    """The mean of a list of numbers."""
    if len(numbers) == 0:
        raise ValueError('I cannot find the average of an empty list.')
    return sum(numbers) / len(numbers)
