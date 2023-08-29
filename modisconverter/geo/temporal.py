import re
from datetime import datetime
from modisconverter.common import log, util

LOGGER = log.get_logger()


class Modis():
    def __init__(self):
        self._inception = datetime(2000, 1, 1, 0, 0, 0)

    @property
    def inception(self):
        return self._inception

    def get_days_since_inception(self, dt):
        LOGGER.debug(f'calculating days between inception {self.inception} and date {dt} ...')
        diff = dt - self._inception
        return diff.days

    def extract_modis_datetime(self, file_name):
        LOGGER.debug(f'extracting date from file_name {file_name} ...')
        # extract the date of a MODIS granule from its filename
        pattern = '\.A(\d{4})(\d{3})\.'
        match = re.search(pattern, file_name)
        if match:
            # get datetime based on the year and day of year
            return util.julian_to_datetime(match.group(1), match.group(2))

        # unable to parse a date
        return None

    def get_netcdf_time_attributes(self):
        return {
            'axis': 'T',
            'calendar': 'julian',
            'units': f'days since {self.inception.strftime("%Y-%m-%d %H:%M:%S")}',
            'standard_name': 'time'
        }
