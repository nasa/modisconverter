import functools
import time
from modisconverter.common import log


LOGGER = log.get_logger()


class Timer():
    def __init__(self):
        self._start, self._end = None, None

    def start(self):
        self._start = time.perf_counter()

    def end(self):
        self._end = time.perf_counter()

    @property
    def duration(self):
        if self._end is not None and self._start is not None:
            return self._end - self._start
        return None


def timeit(f):
    """Decorator to time the execution of a function"""
    @functools.wraps(f)
    def inner(*args, **kwargs):
        start_time = time.perf_counter()
        val = f(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        try:
            # if this function is actually a __call__ method of a decorator class, extract the name
            func_name = args[0].__self__.func.__name__
        except:
            # if we're using a timing wrapper, extract the timed function name
            func_name = args[0].__name__ if f.__name__ == 'time_function' else f.__name__
        LOGGER.debug(f'{func_name!r} completed in {run_time:.4f} secs')

        return val

    return inner


@timeit
def time_function(func, *args, **kwargs):
    """"A wrapper to time an arbitrary function (one that isn't decorated)"""
    return func(*args, **kwargs)


def runtime(func, *args, **kwargs):
    start = time.perf_counter()
    val = func(*args, **kwargs)
    end = time.perf_counter()
    return end - start, val


def function_time_analysis(func, repeat, return_func_val, *args, **kwargs):
    """ Runs a function multiple times and compute statistics on execution times"""
    stats = {'mean': None, 'min': None, 'max': None, 'total': None, 'repeat': repeat}
    func_val_set, func_val = False, None
    exec_times = []
    for _ in range(repeat):
        start_time = time.perf_counter()
        val = func(*args, **kwargs)
        if return_func_val and not func_val_set:
            func_val_set, func_val = True, val
        end_time = time.perf_counter()
        run_time = end_time - start_time
        exec_times.append(run_time)

    def mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    stats['mean'] = mean(exec_times)
    stats['min'] = min(exec_times)
    stats['max'] = max(exec_times)
    stats['total'] = sum(exec_times)

    return stats, func_val
