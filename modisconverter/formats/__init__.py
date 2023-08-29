import math
import numpy as np
import rasterio as rio
import netCDF4
from contextlib import contextmanager
from pyhdf.SD import SD as HdfSd
from pyhdf.SD import SDC
from rasterio.windows import Window
from abc import ABC, abstractmethod, abstractstaticmethod
from modisconverter.common import log

LOGGER = log.get_logger()
FORMAT_NETCDF4, FORMAT_NETCDF4_EXT = 'NetCDF4', 'nc'
FORMAT_HDF4, FORMAT_HDF4_EXT = 'HDF4', 'hdf'
SUPPORTED_FORMATS = {
    FORMAT_NETCDF4: FORMAT_NETCDF4_EXT,
    FORMAT_HDF4: FORMAT_HDF4_EXT
}
MODE_READ, MODE_WRITE, MODE_APPEND = 'r', 'w', 'a'
DEFAULT_MODE = MODE_READ
# a maximum size of a data array in windowed reading/writing
DEFAULT_MAX_WINDOW_BYTES = 1024 * 1024 * 100  # 100 MB
PYHDF_DATA_TYPES = {
    SDC.CHAR: 'char',
    SDC.CHAR8: 'char8',
    SDC.UCHAR8: 'uchar8',
    SDC.INT8: 'int8',
    SDC.UINT8: 'uint8',
    SDC.INT16: 'int16',
    SDC.UINT16: 'uint16',
    SDC.INT32: 'int32',
    SDC.UINT32: 'uint32',
    SDC.FLOAT32: 'float32',
    SDC.FLOAT64: 'float64'
}


@contextmanager
def open_with_rio(src, mode='r', options=None):
    options = {} if options is None else options
    resource = None
    try:
        LOGGER.debug(f'opening {src} using rasterio...')
        resource = rio.open(src, mode=mode, **options)
        yield resource
    except Exception as e:
        raise RasterioReadError(f'{e.__class__.__name__}: {str(e)}')
    finally:
        if resource is not None and not resource.closed:
            LOGGER.debug(f'closing {src} ...')
            resource.close()


@contextmanager
def open_with_netcdf4(src, mode='r', options=None):
    options = {} if options is None else options
    resource = None
    try:
        LOGGER.debug(f'opening {src} using netCDF4...')
        resource = netCDF4.Dataset(src, mode=mode, **options)
        yield resource
    except Exception as e:
        raise NetCdf4ReadError(f'{e.__class__.__name__}: {str(e)}')
    finally:
        if resource is not None and resource.isopen:
            LOGGER.debug(f'closing {src} ...')
            resource.close()


@contextmanager
def open_with_pyhdf(src):
    resource = None
    try:
        LOGGER.debug(f'opening {src} using pyhdf...')
        resource = HdfSd(src)
        yield resource
    except Exception as e:
        raise NetCdf4ReadError(f'{e.__class__.__name__}: {str(e)}')
    finally:
        if resource is not None:
            LOGGER.debug(f'closing {src} ...')
            resource.end()


def file_has_ext(file_name, ext):
    return file_name.endswith(f'.{ext}')


class RasterioReadError(Exception):
    """A general class for any issues opening a dataset with rasterio"""


class NetCdf4ReadError(Exception):
    """A general class for any issues opening a dataset with netcdf4"""


class RasterError(Exception):
    """A general class for any issues pertaining to rasters, including conversion and calculation"""


class OpenDataset():
    def __init__(self, ds, mode):
        self._ds = ds
        self._mode = mode

    def __str__(self):
        return f'{type(self)}\ndataset: {self.ds}\nmode: {self.mode}'

    @property
    def ds(self):
        return self._ds

    @property
    def mode(self):
        return self._mode


class FileFormat(ABC):
    @property
    def format(self):
        return self._format

    @property
    def extension(self):
        return self._ext

    @property
    def file_name(self):
        return self._file_name

    @property
    def mode(self):
        return self._mode

    def __str__(self):
        return f'{self.__class__.__name__} with file {self.file_name}'

    def __repr__(self):
        return f'{self.__module__}.{self.__class__.__name__}(\'{self.file_name}\')'

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _open(self):
        pass

    @abstractstaticmethod
    def validate_file_ext(file_name):
        pass


class RasterUtil():
    @staticmethod
    def generate_windows(data_shape, window_shape):
        data_y_size, data_x_size = data_shape
        win_y_size, win_x_size = window_shape

        for y_idx in range(0, data_y_size, win_y_size):
            height = win_y_size if y_idx + win_y_size <= data_y_size else data_y_size - y_idx
            for x_idx in range(0, data_x_size, win_x_size):
                width = win_x_size if x_idx + win_x_size <= data_x_size else data_x_size - x_idx
                LOGGER.debug(f'creating window with x offset {x_idx}, y offset {y_idx}, width {width}, height {height} ...')

                yield Window(x_idx, y_idx, width, height)

    @staticmethod
    def calculate_window_shape(data_shape, data_type, window_dims=None, window_by_max_bytes=None):
        """
        Calculates the proper window shape in context of the data.

        Args:
            data_shape (tuple): the 2D shape of the data
            data_type (string): the data shape represented as a string identifier
            window_dims (tuple): ints defining the shape of the windows.
            window_by_max_bytes (int):
                defines the maximum amount of space, in bytes, to be used for
                a window. The window dimensions are estimated to keep at or
                below this value.
        Returns:
            window_y_size, window_x_size (tuple): a shape (dimensions) for the window
        Raises:
            (ValueError): for any provided params fail validation
        """
        if not window_dims and not window_by_max_bytes:
            raise ValueError(
                'neither window_dims nor window_by_max_bytes was provided'
            )

        data_y_size, data_x_size = data_shape
        window_y_size, window_x_size, dim_y_size, dim_x_size = None, None, None, None
        if window_dims:
            # validate the dimensions specified for the window
            if not isinstance(window_dims, tuple):
                raise ValueError('window_dims must be a tuple of integers')
            num_win_dims = len(window_dims)
            num_data_dims = len(data_shape)
            if num_win_dims != num_data_dims:
                raise ValueError(f'window_dims shape, which has {num_win_dims} '
                                 f'dimensions, does not match the shape of the '
                                 f'data, which has {num_data_dims} dimensions')

            invalid_dims = [{'idx': idx, 'val': d_size}
                            for idx, d_size in enumerate(window_dims)
                            if not isinstance(d_size, int) or d_size < 1]
            if invalid_dims:
                dim_stmt = ', '. join([
                    f'dimension {item["idx"]} has value {item["val"]}'
                    for item in invalid_dims])
                raise ValueError('window_dims contains the following invalid '
                                 f'dimensions: {dim_stmt}. dimension values '
                                 'must be positive integers 1 or greater')

            dim_y_size, dim_x_size = window_dims[0], window_dims[1]
        elif window_by_max_bytes:
            # calculate a window with square dimensions that
            # stay within the maximum size
            dtype = np.dtype(data_type)
            dt_byte_size = dtype.itemsize  # size in bytes of the data type
            max_num_items_in_win = int(window_by_max_bytes / dt_byte_size)
            dim_size = int(math.sqrt(max_num_items_in_win))
            dim_y_size, dim_x_size = dim_size, dim_size

        # resize any window dimensions that are outside of the data bounds
        window_y_size = dim_y_size if dim_y_size <= data_y_size else data_y_size
        window_x_size = dim_x_size if dim_x_size <= data_x_size else data_x_size

        return window_y_size, window_x_size

    @staticmethod
    def get_data_indexes_from_window(window):
        if window and not isinstance(window, Window):
            raise ValueError('window is not a rasterio.windows.Window object')

        y_start, y_end = window.row_off, window.row_off + window.height
        x_start, x_end = window.col_off, window.col_off + window.width

        return ((y_start, y_end), (x_start, x_end))

    @staticmethod
    def cast_value_by_dtype(value, dtype):
        return np.cast[dtype](value)

    @staticmethod
    def recast_array(arr, dtype, in_place=True):
        if arr.dtype == dtype:
            # no need to recast
            return arr
        else:
            try:
                return arr.astype(dtype, copy=not in_place)
            except Exception as e:
                raise RasterError(f'Unable to recast array to {dtype}. {str(e)}')

    @staticmethod
    def replace_nan_in_array(arr, replacement, in_place=True):
        try:
            return np.nan_to_num(arr, nan=replacement, copy=not in_place)
        except Exception as e:
            raise RasterError(f'Unable to replace NaN values with value {replacement}. {str(e)}')

    @staticmethod
    def pyhdf_dtype_to_numpy_dtype(pyhdf_dtype_id):
        if pyhdf_dtype_id not in PYHDF_DATA_TYPES:
            raise ValueError(f'pyhdf dtype identifier {pyhdf_dtype_id} is unknown')
        try:
            return np.dtype(PYHDF_DATA_TYPES[pyhdf_dtype_id])
        except:
            raise RasterError(
                'Unable to create a numpy dtype from the pyhdf dtype '
                f'{pyhdf_dtype_id}'
            )
