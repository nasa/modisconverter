import os
import logging
import datetime
from dateutil.tz import tzlocal

LOGGER_NAME = 'modisconverter'
LOG_FORMAT = '%(asctime)s\t%(levelname)s\t%(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f %z'
LOG_LEVEL = logging.INFO
LOG_LEVEL_ENV_VAR = 'MFC_LOG_LEVEL'


def get_logger(log_level=LOG_LEVEL):
    """
    Creates a stream-based logger

    Args:
        log_level (int):   logging level, defaults to INFO.
            However, should the env var MFC_LOG_LEVEL be present
            it will be used.

    Returns:
        logger (logging.Logger): a stream logger object
    """
    if env_log_level := os.environ.get(LOG_LEVEL_ENV_VAR, None):
        log_level = int(env_log_level)

    if LOGGER_NAME in logging.root.manager.loggerDict:
        # the logger already exists, simply return it
        return logging.getLogger(LOGGER_NAME)

    # configure a stream handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        LogFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )

    # create the logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.addHandler(console_handler)
    logger.setLevel(log_level)

    return logger


class LogFormatter(logging.Formatter):
    """
    A custom class to support date formats with microseconds and
    local timezone (zone, offset, etc.)
    """
    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        # inject the system timezone
        local_tz = tzlocal()
        ct = self.converter(record.created).replace(tzinfo=local_tz)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime('%Y-%m-%d %H:%M:%S')
            s = "%s,%03d" % (t, record.msecs)
        return s
