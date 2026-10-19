"""Time and dates in plain English."""
import datetime as _datetime
import time as _time

raw = _time


def wait(seconds):
    """Pauses the program for this many seconds."""
    _time.sleep(seconds)


def seconds_now():
    """The number of seconds since 1 January 1970. Use it to time things."""
    return _time.time()


def start_timer():
    """Starts a timer. Keep the result and give it to seconds_since later."""
    return _time.perf_counter()


def seconds_since(timer):
    """How many seconds have passed since start_timer gave you this timer."""
    return _time.perf_counter() - timer


def today():
    """Today's date as text, like 2026-10-07."""
    return _datetime.date.today().isoformat()


def time_now():
    """The time now as text, like 14:30:05."""
    return _datetime.datetime.now().strftime('%H:%M:%S')


def year_now():
    """The current year."""
    return _datetime.date.today().year


def month_now():
    """The current month as a number from 1 to 12."""
    return _datetime.date.today().month


def day_now():
    """The day of the month, from 1 to 31."""
    return _datetime.date.today().day


def weekday_name():
    """The name of today, like Wednesday."""
    return _datetime.date.today().strftime('%A')
