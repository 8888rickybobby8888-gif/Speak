"""matplotlib in plain English: draw charts.

Typical use:
    use matplotlib
    matplotlib.line_chart([1, 2, 3], [2, 4, 8], "growth")
    matplotlib.title("My chart")
    matplotlib.show_chart()
"""
import matplotlib.pyplot as _plot

raw = _plot


def new_chart(width=8, height=5):
    """Starts a new empty chart of this size in inches."""
    _plot.figure(figsize=(width, height))


def line_chart(x_values, y_values, label=None):
    """Draws a line through the points."""
    _plot.plot(x_values, y_values, label=label)


def bar_chart(names, heights, label=None):
    """Draws one bar for each name."""
    _plot.bar(names, heights, label=label)


def scatter_chart(x_values, y_values, label=None):
    """Draws a dot at each point."""
    _plot.scatter(x_values, y_values, label=label)


def histogram(values, bars=10):
    """Draws how many of the values fall into each of this many bars."""
    _plot.hist(values, bins=bars)


def pie_chart(names, amounts):
    """Draws a pie with a slice for each name."""
    _plot.pie(amounts, labels=names, autopct='%1.0f%%')


def title(text):
    """Sets the title shown above the chart."""
    _plot.title(text)


def x_label(text):
    """Sets the label under the horizontal axis."""
    _plot.xlabel(text)


def y_label(text):
    """Sets the label beside the vertical axis."""
    _plot.ylabel(text)


def legend():
    """Shows a key for the labelled lines and bars."""
    _plot.legend()


def grid():
    """Shows grid lines behind the chart."""
    _plot.grid(True)


def set_x_range(lowest, highest):
    """Sets the part of the horizontal axis that is shown."""
    _plot.xlim(lowest, highest)


def set_y_range(lowest, highest):
    """Sets the part of the vertical axis that is shown."""
    _plot.ylim(lowest, highest)


def show_chart():
    """Opens a window showing the chart. The program waits until it is closed."""
    _plot.show()


def save_chart(filename):
    """Saves the chart as a picture file, for example "chart.png"."""
    _plot.savefig(filename)


def close_chart():
    """Closes the chart and forgets what was drawn."""
    _plot.close()
