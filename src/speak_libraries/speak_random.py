"""Random choices in plain English."""
import random as _random

raw = _random


def whole_number(lowest, highest):
    """A random whole number from lowest to highest, both included."""
    return _random.randint(lowest, highest)


def decimal_number():
    """A random decimal number from 0 up to (not including) 1."""
    return _random.random()


def pick_one(items):
    """One random item from a list."""
    if len(items) == 0:
        raise ValueError('I cannot pick from an empty list.')
    return _random.choice(items)


def pick_several(items, how_many):
    """A new list of how_many different random items from a list."""
    if how_many > len(items):
        raise ValueError(f'I cannot pick {how_many} items from a list of {len(items)}.')
    return _random.sample(list(items), how_many)


def shuffle(items):
    """Puts the items of a list in a random order (changes the list itself)."""
    _random.shuffle(items)


def shuffled_copy(items):
    """A new list with the same items in a random order."""
    copy = list(items)
    _random.shuffle(copy)
    return copy


def coin_flip():
    """Either "heads" or "tails"."""
    return _random.choice(['heads', 'tails'])


def roll_dice(sides=6):
    """A random whole number from 1 up to the number of sides (6 unless you say otherwise)."""
    return _random.randint(1, sides)


def chance(percent):
    """True this often: chance(25) is true about one time in four."""
    return _random.random() * 100 < percent
