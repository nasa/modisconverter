import os
from functools import partial
from contextlib import contextmanager
from modisconverter.formats import (
    FileFormat, RasterUtil, OpenDataset, open_with_rio, open_with_pyhdf,
    file_has_ext, FORMAT_HDF4, FORMAT_HDF4_EXT,
    DEFAULT_MODE, MODE_READ
)
from modisconverter.formats.netcdf import NetCdf4
from modisconverter.common import log


LOGGER = log.get_logger()
SUPPORTED_MODES = [MODE_READ]


class Hdf4(FileFormat):
    def __init__(self, file_name, mode=DEFAULT_MODE):
        self._file_name = file_name
        self._open_dataset = None
        self._format = FORMAT_HDF4
        self._ext = FORMAT_HDF4_EXT
        Hdf4.validate_file_ext(self.file_name)
        self._set_mode(mode)
        self._setup()

    @staticmethod
    def validate_file_ext(file_name):
        if not file_has_ext(file_name, FORMAT_HDF4_EXT):
            raise ValueError(f'file {file_name} does not have the correct extension, {"." + FORMAT_HDF4_EXT}')

    def _set_mode(self, mode):
        self._mode = mode

        if self.mode not in SUPPORTED_MODES:
            raise ValueError(f'mode \'{self.mode}\' is not supported. Please use one of the following: {SUPPORTED_MODES}')
        if self.mode in [MODE_READ] and not os.path.exists(self.file_name):
            raise Hdf4Error(f'file {self.file_name} does not exist (mode is \'{self.mode}\').')

    def _setup(self):
        self._subdatasets = []
        self._crs = None
        self._shape = None
        with self._open() as ds:
            self._shape = ds.shape
            transform = ds.transform
            crs = ds.crs
            for sds_name in ds.subdatasets:
                sds = HdfSubdataset(sds_name, self.file_name)
                if sds.crs and not crs:
                    # use the CRS and transform of this SDS as the file's CRS and transform
                    LOGGER.debug(
                        f'using CRS and tranform of subdataset {sds_name} as the file\'s CRS and transform')
                    crs = sds.crs
                    transform = sds.transform
                self._subdatasets.append(sds)
            self._crs = crs
            self._transform = transform

    def __str__(self):
        return f'{self.__class__.__name__} with file {self.file_name}'

    def __repr__(self):
        return f'{self.__module__}.{self.__class__.__name__}(\'{self.file_name}\')'

    @property
    def subdatasets(self):
        return self._subdatasets

    @property
    def crs(self):
        return self._crs

    @property
    def transform(self):
        return self._transform

    def get_geotransform(self):
        return ' '.join([str(i) for i in self.transform.to_gdal()])

    @property
    def shape(self):
        return self._shape

    @contextmanager
    def _open(self, mode=None):
        if self._open_dataset is not None and (mode is None or self._open_dataset.mode == mode):
            LOGGER.debug(f'using existing open dataset {self._open_dataset}')
            yield self._open_dataset.ds
        else:
            src = self.file_name
            # force the mode if given
            mode = mode if mode is not None else self.mode
            with open_with_rio(src) as ds:
                try:
                    self._open_dataset = OpenDataset(ds, mode)
                    yield ds
                finally:
                    self._open_dataset = None

    def get_attributes(self):
        # use pyhdf, as top-level attributes of this format can't be read by rasterio
        with open_with_pyhdf(self.file_name) as ds:
            return ds.attributes()

    def convert(self, scheme, file_name, replace=True):
        if scheme == 'MODIS_HDF4_to_NetCDF4':
            if not replace and os.path.exists(file_name):
                raise ValueError(f'file {file_name} already exists and convert '
                                 f'process is not set for replacement.')
            elif replace and os.path.exists(file_name):
                LOGGER.debug(f'replacing existing file {file_name} ...')
                os.remove(file_name)

            nc = NetCdf4(file_name, mode='w')
            nc.create_from_data_file(self, scheme)
        else:
            raise ValueError(f'scheme {scheme} is not supported')


class HdfSubdataset():
    def __init__(self, name, file_name):
        self._name = name
        self._file_name = file_name
        self._setup()

    def __str__(self):
        return f'{self.__class__.__name__} with name {self.name}'

    def __repr__(self):
        return (f'{self.__module__}.{self.__class__.__name__}(\'{self.name}\', '
                f'{self.crs.__class__}, {self.shape})')

    def _setup(self):
        self._name_layer_separator = ':'
        self._default_band_num = 1
        with self._open() as ds:
            self._crs = ds.crs
            self._transform = ds.transform
            num_dim = len(ds.shape)
            if num_dim != 2:
                raise Hdf4Error(f'data shape must be 2D, but the data has '
                                f'{num_dim} dimensions (shape: {ds.shape})')
            num_bands = len(ds.dtypes)
            if num_bands != 1:
                raise Hdf4Error(f'there must be only one band for the subdataset, '
                                f'but {num_bands} are present')
            self._shape = ds.shape
            self._dtype = ds.dtypes[0]

    @property
    def name(self):
        return self._name

    @property
    def file_name(self):
        return self._file_name

    @property
    def layer_name(self):
        return self._name.split(':')[-1]

    @property
    def crs(self):
        return self._crs

    @property
    def transform(self):
        return self._transform

    def get_geotransform(self):
        return ' '.join([str(i) for i in self.transform.to_gdal()])

    @property
    def shape(self):
        return self._shape

    @property
    def dtype(self):
        return self._dtype

    @contextmanager
    def _open(self):
        with open_with_rio(self.name) as ds:
            yield ds

    def get_src_info(self):
        # use pyhdf to get certain source data; rasterio may implicitly cast
        # some data types - namely, int8 to uint8 - and discard the original fill
        # value that is outside the new type
        with open_with_pyhdf(self.file_name) as ds:
            sds = ds.select(self.layer_name)
            return {
                'dtype': RasterUtil.pyhdf_dtype_to_numpy_dtype(sds.info()[3]),
                'fill_value': sds.getfillvalue(),
                'attributes': sds.attributes()
            }

    def data(self):
        """
        Returns the data for the SDS.

        Returns:
            (numpy.ndarray): the data array
        """
        with self._open() as ds:
            return ds.read(self._default_band_num)

    def data_by_windows(self, window_dims=None, window_by_max_bytes=None, data_as_partial=False):
        """
        A generator for returning data in rectilinear windows, which effectively
        provides data in a chunked manner for efficient I/O.

        Args:
            window_dims (tuple): ints defining the shape of the windows.
            window_by_max_bytes (int):
                defines the maximum amount of space, in bytes, to be used for
                a window. The window dimensions are estimated to keep at or
                below this value.
            data_as_partial (bool):
                True to return the data as a partial. This allows for the reading
                of window data at a later time.  False to return the data as a
                numpy.ndarray.
        Yields:
            window, data (tuple)
                window (rasterio.windows.Window): the window object for the chunk
                data (numpy.ndarray or functools.partial): the data array, or
                    a partial to later read the data into an array

        Raises:
            (ValueError): for any provided params fail validation
        """
        # calculate the proper window shape
        window_shape = RasterUtil.calculate_window_shape(
            self.shape, self.dtype, window_dims=window_dims,
            window_by_max_bytes=window_by_max_bytes)

        with self._open() as ds:
            # create the windows and their data for the dataset
            for window in RasterUtil.generate_windows(self.shape, window_shape):
                if data_as_partial:
                    data = partial(ds.read, self._default_band_num, window=window)
                else:
                    data = ds.read(self._default_band_num, window=window)

                yield window, data


class Hdf4Error(Exception):
    """A general class for issues with HDF 4 files (data, etc.)"""
    pass
