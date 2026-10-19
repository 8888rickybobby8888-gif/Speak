"""numpy in plain English: number crunching with arrays, with no abbreviations.

Angles are in degrees. Positions returned by position_of_smallest and position_of_largest
count from 1, so you can use them with "item N of". The original library is available as `raw`.
Constants: pi
"""
import numpy as _numpy

raw = _numpy
pi = _numpy.pi


# ---- making arrays

def array(values):
    """Turns a list into an array, which you can do maths on all at once."""
    return _numpy.array(values)


def zeros(shape):
    """An array full of 0. The shape is a count, or (rows, columns)."""
    return _numpy.zeros(shape)


def ones(shape):
    """An array full of 1. The shape is a count, or (rows, columns)."""
    return _numpy.ones(shape)


def filled_with(shape, value):
    """An array of this shape with every item set to the value."""
    return _numpy.full(shape, value)


def identity_matrix(size):
    """A square grid with 1 down the diagonal and 0 everywhere else."""
    return _numpy.identity(size)


def numbers_from_to(first, last, step=1):
    """The numbers from first to last, both included, counting up by step (like a Speak for loop)."""
    if step == 0:
        raise ValueError('The step cannot be zero.')
    count = int(_numpy.floor((last - first) / step + 1e-9)) + 1
    return first + step * _numpy.arange(max(count, 0))


def evenly_spaced(first, last, how_many):
    """How_many numbers spread evenly from first to last, both included."""
    return _numpy.linspace(first, last, how_many)


def random_decimals(how_many):
    """An array of random decimal numbers from 0 up to (not including) 1."""
    return _numpy.random.random(how_many)


def random_whole_numbers(lowest, highest, how_many):
    """An array of random whole numbers from lowest to highest, both included."""
    return _numpy.random.randint(lowest, highest + 1, how_many)


def list_of(values):
    """Turns an array back into an ordinary list."""
    return _numpy.asarray(values).tolist()


# ---- the shape of an array

def shape_of(values):
    """The size of each dimension, for example (rows, columns)."""
    return _numpy.shape(values)


def number_of_items(values):
    """How many items the array holds in total."""
    return _numpy.size(values)


def rows_of(grid):
    """How many rows a grid has."""
    return _numpy.shape(grid)[0]


def columns_of(grid):
    """How many columns a grid has."""
    return _numpy.shape(grid)[1]


def reshape(values, rows, columns):
    """The same items arranged in a grid with this many rows and columns."""
    return _numpy.reshape(values, (rows, columns))


def transpose(grid):
    """The grid flipped so rows become columns."""
    return _numpy.transpose(grid)


def join(first, second):
    """One array made by putting the second after the first."""
    return _numpy.concatenate([first, second])


def row_of(grid, number):
    """One row of a grid. Rows count from 1."""
    return grid[number - 1]


def column_of(grid, number):
    """One column of a grid. Columns count from 1."""
    return grid[:, number - 1]


# ---- statistics

def total(values):
    """All the numbers added together."""
    return _numpy.sum(values)


def mean(values):
    """The average of the numbers."""
    return _numpy.mean(values)


def median(values):
    """The middle number once they are in order."""
    return _numpy.median(values)


def standard_deviation(values):
    """How spread out the numbers are."""
    return _numpy.std(values)


def variance(values):
    """The standard deviation squared."""
    return _numpy.var(values)


def smallest(values):
    """The smallest number."""
    return _numpy.min(values)


def largest(values):
    """The largest number."""
    return _numpy.max(values)


def position_of_smallest(values):
    """Where the smallest number is, counting from 1."""
    return int(_numpy.argmin(values)) + 1


def position_of_largest(values):
    """Where the largest number is, counting from 1."""
    return int(_numpy.argmax(values)) + 1


def percentile(values, percent):
    """The number that this percent of the values fall below."""
    return _numpy.percentile(values, percent)


def correlation(first, second):
    """How closely two sets of numbers move together, from -1 to 1."""
    return _numpy.corrcoef(first, second)[0, 1]


def cumulative_total(values):
    """The running total: each item is the sum of everything so far."""
    return _numpy.cumsum(values)


def sorted_copy(values):
    """A new array with the numbers in order, smallest first."""
    return _numpy.sort(values)


def reversed_copy(values):
    """A new array with the items in the opposite order."""
    return _numpy.asarray(values)[::-1]


def unique_values(values):
    """The different values that appear, in order, with no repeats."""
    return _numpy.unique(values)


def how_many_equal(values, target):
    """How many items are equal to the target."""
    return int(_numpy.sum(_numpy.asarray(values) == target))


def all_true(conditions):
    """True if every item is true."""
    return bool(_numpy.all(conditions))


def any_true(conditions):
    """True if at least one item is true."""
    return bool(_numpy.any(conditions))


# ---- maths on every item

def square_root(values):
    """The square root of every number."""
    return _numpy.sqrt(values)


def absolute(values):
    """Every number without its minus sign."""
    return _numpy.abs(values)


def power(values, exponent):
    """Every number multiplied by itself exponent times."""
    return _numpy.power(values, exponent)


def exponential(values):
    """e raised to the power of every number."""
    return _numpy.exp(values)


def natural_logarithm(values):
    """The logarithm to the base e of every number."""
    return _numpy.log(values)


def sine(degrees):
    """The sine of every angle, given in degrees."""
    return _numpy.sin(_numpy.radians(degrees))


def cosine(degrees):
    """The cosine of every angle, given in degrees."""
    return _numpy.cos(_numpy.radians(degrees))


def tangent(degrees):
    """The tangent of every angle, given in degrees."""
    return _numpy.tan(_numpy.radians(degrees))


def round_to(values, places=0):
    """Every number rounded to this many decimal places."""
    return _numpy.round(values, places)


def round_down(values):
    """Every number rounded down to a whole number."""
    return _numpy.floor(values)


def round_up(values):
    """Every number rounded up to a whole number."""
    return _numpy.ceil(values)


def larger_of_each(first, second):
    """For each pair of items, the larger one."""
    return _numpy.maximum(first, second)


def smaller_of_each(first, second):
    """For each pair of items, the smaller one."""
    return _numpy.minimum(first, second)


# ---- grids and vectors

def dot_product(first, second):
    """Multiplies matching items of two lists of numbers and adds them up."""
    return _numpy.dot(first, second)


def matrix_product(first, second):
    """The matrix multiplication of two grids (the same as first @ second)."""
    return _numpy.matmul(first, second)


def determinant(grid):
    """The determinant of a square grid."""
    return _numpy.linalg.det(grid)


def inverse(grid):
    """The inverse of a square grid."""
    return _numpy.linalg.inv(grid)
