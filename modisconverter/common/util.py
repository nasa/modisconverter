import os
from datetime import datetime
from dateutil import tz


def join_and_normalize(*args):
    """
    Construct a normalized path from joined paths for a file system

    Args:
        args: one or more strings to join

    Returns:
        (str): a joined and normalized file path
    """
    return os.path.normpath(os.path.join(*args))


def split_path(path):
    return [i for i in path.split('/') if i]


def get_current_datetime(tz=tz.UTC, format='%Y-%m-%dT%H:%M:%SZ'):
    return datetime.now(tz).strftime(format)


def julian_to_datetime(year, day_of_year):
    return datetime.strptime(f'{year}{day_of_year}', '%Y%j')
