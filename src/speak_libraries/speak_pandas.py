"""pandas in plain English: tables of data.

A table has named columns and numbered rows. Typical use:
    use pandas
    people = pandas.make_table({"name": ["Ada", "Alan"], "age": [36, 41]})
    print pandas.average_of_column(people, "age")
"""
import pandas as _pandas

raw = _pandas


def make_table(data):
    """A table from a dictionary of columns, like {"name": [...], "age": [...]}."""
    return _pandas.DataFrame(data)


def read_table(filename):
    """Reads a table from a CSV file."""
    return _pandas.read_csv(filename)


def save_table(table, filename):
    """Saves the table to a CSV file."""
    table.to_csv(filename, index=False)


def first_rows(table, how_many=5):
    """The first rows of the table."""
    return table.head(how_many)


def last_rows(table, how_many=5):
    """The last rows of the table."""
    return table.tail(how_many)


def number_of_rows(table):
    """How many rows the table has."""
    return len(table)


def column_names(table):
    """The names of the columns, as a list."""
    return list(table.columns)


def column_of(table, name):
    """One column of the table."""
    if name not in table.columns:
        raise ValueError(f'The table has no column called "{name}". Its columns are: {", ".join(map(str, table.columns))}.')
    return table[name]


def add_column(table, name, values):
    """A new table with an extra column."""
    return table.assign(**{name: values})


def average_of_column(table, name):
    """The mean of the numbers in a column."""
    return column_of(table, name).mean()


def total_of_column(table, name):
    """The sum of the numbers in a column."""
    return column_of(table, name).sum()


def largest_in_column(table, name):
    """The biggest value in a column."""
    return column_of(table, name).max()


def smallest_in_column(table, name):
    """The smallest value in a column."""
    return column_of(table, name).min()


def sort_table(table, name, largest_first=False):
    """A new table with its rows in order of one column."""
    return table.sort_values(name, ascending=not largest_first)


def rows_where(table, name, value):
    """The rows where this column is equal to the value."""
    return table[column_of(table, name) == value]


def rows_above(table, name, value):
    """The rows where this column is greater than the value."""
    return table[column_of(table, name) > value]


def rows_below(table, name, value):
    """The rows where this column is less than the value."""
    return table[column_of(table, name) < value]


def total_by_group(table, group_column, value_column):
    """For each different value in one column, the total of another column."""
    return table.groupby(group_column)[value_column].sum()


def summary_of(table):
    """Counts, averages and ranges for every number column."""
    return table.describe()


def remove_missing(table):
    """A new table without any row that has a missing value."""
    return table.dropna()
