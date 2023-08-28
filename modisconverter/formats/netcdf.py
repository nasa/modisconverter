import os
import re
import functools
import numpy as np
from contextlib import contextmanager
from functools import partial
from urllib.parse import urljoin
from rasterio.windows import Window
from modisconverter.common import log, util, version
from modisconverter.common import timing
from modisconverter.formats import (
    FileFormat, RasterUtil, OpenDataset, open_with_netcdf4, file_has_ext,
    FORMAT_NETCDF4, FORMAT_NETCDF4_EXT, FORMAT_HDF4, DEFAULT_MODE, MODE_READ,
    MODE_WRITE, MODE_APPEND, DEFAULT_MAX_WINDOW_BYTES
)
from modisconverter.geo import spatial, temporal


LOGGER = log.get_logger()
DEFAULT_YDIM_DIMENSION = 'ydim'
DEFAULT_YDIM_ATTRIBUTES = {
    '_CoordinateAxisType': 'GeoY',
    'axis': 'Y'
}
DEFAULT_XDIM_DIMENSION = 'xdim'
DEFAULT_XDIM_ATTRIBUTES = {
    '_CoordinateAxisType': 'GeoX',
    'axis': 'X'
}
DEFAULT_SPATIAL_DIMENSION_DTYPE = np.dtype('float64')
DEFAULT_TIME_DIMENSION = 'time'
DEFAULT_TEMPORAL_DIMENSION_DTYPE = np.dtype('int')
DEFAULT_CRS_VAR = 'crs'
DEFAULT_CRS_VAR_DTYPE = np.dtype('c')
DEFAULT_NETCDF4_VARIABLE_OPTIONS = {
    'zlib': True,
    'complevel': 4,
    'shuffle': True
}
DEFAULT_GLOBAL_ATTRIBUTES = {
    'Conventions': 'CF-1.7',
    'institution': 'Land Processes Distributed Active Archive Center (LP DAAC)',
    'source': version.get_library_identifier()
}

SUPPORTED_MODES = [MODE_READ, MODE_WRITE, MODE_APPEND]


def assert_writable(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        inst = args[0]
        if inst.mode not in [MODE_WRITE, MODE_APPEND]:
            raise NetCdf4Error(f'object is not writable (mode: {inst.mode})')
        return f(*args, **kwargs)

    return inner


class NetCdf4(FileFormat):
    def __init__(self, file_name, mode=DEFAULT_MODE):
        self._file_name = file_name
        self._open_dataset = None
        self._format = FORMAT_NETCDF4
        self._ext = FORMAT_NETCDF4_EXT
        NetCdf4.validate_file_ext(self.file_name)
        self._set_mode(mode)
        self._setup()

    @staticmethod
    def validate_file_ext(file_name):
        if not file_has_ext(file_name, FORMAT_NETCDF4_EXT):
            raise ValueError(f'file {file_name} does not have the correct extension, {"." + FORMAT_NETCDF4_EXT}')

    def _set_mode(self, mode):
        self._mode = mode

        if self.mode not in SUPPORTED_MODES:
            raise ValueError(f'mode \'{self.mode}\' is not supported. Please use one of the following: {SUPPORTED_MODES}')
        if self.mode in [MODE_READ, MODE_APPEND] and not os.path.exists(self.file_name):
            raise NetCdf4Error(f'file {self.file_name} does not exist (mode is \'{self.mode}\').')
        if self.mode == MODE_WRITE:
            if os.path.exists(self.file_name):
                # overwrite, so delete the file
                os.remove(self.file_name)
            # create the file
            with self._open(mode=self.mode):
                pass

    def _setup(self):
        pass

    def __str__(self):
        with self._open(mode='r') as ds:
            return str(ds)

    @property
    def dimensions(self):
        with self._open(mode='r') as ds:
            return ds.dimensions

    @property
    def variables(self):
        with self._open(mode='r') as ds:
            return ds.variables

    @property
    def groups(self):
        with self._open(mode='r') as ds:
            return ds.groups

    @contextmanager
    def _open(self, mode=None):
        if self._open_dataset is not None and (mode is None or self._open_dataset.mode == mode):
            # LOGGER.debug(f'using existing open dataset {self._open_dataset}')
            yield self._open_dataset.ds
        else:
            src = self.file_name
            # force the mode if given
            mode = mode if mode is not None else self.mode
            options = {'format': 'NETCDF4'}
            with open_with_netcdf4(src, mode=mode, options=options) as ds:
                try:
                    self._open_dataset = OpenDataset(ds, mode)
                    yield ds
                finally:
                    self._open_dataset = None

    def get_variable(self, name):
        parts = util.split_path(name)
        num_parts = len(parts)
        with self._open() as ds:
            try:
                for i, part in enumerate(parts):
                    if i < num_parts - 1:
                        ds = ds.groups[part]
                    else:
                        return ds.variables[part]
            except KeyError:
                raise NetCdf4Error(f'variable {name} does not exist in the dataset')

    def get_group(self, name):
        parts = util.split_path(name)
        num_parts = len(parts)
        with self._open() as ds:
            try:
                for i, part in enumerate(parts):
                    if i < num_parts - 1:
                        ds = ds.groups[part]
                    else:
                        return ds.groups[part]
            except KeyError:
                raise NetCdf4Error(f'group {name} does not exist in the dataset')

    def get_variable_data(self, name):
        """
        Returns the data for the variable.

        Args:
            name (str): the name of the variable
        Returns:
            (numpy.ndarray): the data array
        """
        with self._open():
            var = self.get_variable(name)

            return var[:]

    def get_variable_data_by_windows(self, name, window_dims=None, window_by_max_bytes=None, data_as_partial=False):
        """
        A generator for returning data in rectilinear windows, which effectively
        provides data in a chunked manner for efficient I/O.

        Args:
            name (str): the name of the variable
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
            (NetCdf4Error): if the variable doesn't exist
            (ValueError): for any provided params fail validation
        """
        def _read_data(var, y_start, y_end, x_start, x_end):
            return var[y_start:y_end, x_start:x_end]

        with self._open():
            var = self.get_variable(name)

            # calculate the proper window shape
            window_shape = RasterUtil.calculate_window_shape(
                var.shape, var.dtype, window_dims=window_dims,
                window_by_max_bytes=window_by_max_bytes)

            # create the windows and their data for the dataset
            for window in RasterUtil.generate_windows(var.shape, window_shape):
                data_idxs = RasterUtil.get_data_indexes_from_window(window)
                y_start, y_end = data_idxs[0]
                x_start, x_end = data_idxs[1]
                if data_as_partial:
                    data = partial(_read_data, var, y_start, y_end, x_start, x_end)
                else:
                    data = _read_data(var, y_start, y_end, x_start, x_end)

                yield window, data

    @assert_writable
    def add_dimension(self, name, length, group=None):
        with self._open() as ds:
            if group:
                ds = self.get_group(group)

            if name in ds.dimensions:
                raise NetCdf4Error(f'dimension {name} already exists in the dataset/group')
            try:
                ds.createDimension(name, length)
            except Exception as e:
                raise NetCdf4Error(f'{e.__class__.__name__}: {str(e)}')

    @staticmethod
    def _get_cf_compliant_name(name):
        non_alphanumeric = re.compile('\W')
        return non_alphanumeric.sub('_', name)

    @staticmethod
    def _ensure_cf_compliant_dtype(dtype):
        if dtype == np.uint8:
            dtype = np.dtype(np.int16)
        elif dtype == np.uint16:
            dtype = np.dtype(np.int32)
        elif dtype == np.uint32:
            dtype = np.dtype(np.int64)

        return dtype

    @assert_writable
    def add_variable(self, name, dtype, set_auto_mask_scale=None, options=DEFAULT_NETCDF4_VARIABLE_OPTIONS):
        if options is None:
            options = {}
        with self._open() as ds:
            try:
                var = self.get_variable(name)
            except:
                var = None
            if var is not None:
                raise NetCdf4Error(f'variable {name} already exists in the dataset')

            try:
                var = ds.createVariable(name, dtype, **options)
                if set_auto_mask_scale is not None:
                    var.set_auto_maskandscale(set_auto_mask_scale)
            except Exception as e:
                raise NetCdf4Error(f'{e.__class__.__name__}: {str(e)}')

    @assert_writable
    def add_group(self, name):
        with self._open() as ds:
            if name in ds.groups:
                raise NetCdf4Error(f'group {name} already exists in the dataset')
            try:
                ds.createGroup(name)
            except Exception as e:
                raise NetCdf4Error(f'{e.__class__.__name__}: {str(e)}')

    @assert_writable
    def add_data_to_variable(self, name, data, higher_dim_idxs=None, window=None):
        if not isinstance(data, np.ndarray):
            raise ValueError('data is not a numpy array')
        if window and not isinstance(window, Window):
            raise ValueError('window is not a rasterio.windows.Window object')

        if not higher_dim_idxs:
            higher_dim_idxs = []

        with self._open():
            var = self.get_variable(name)

            # write the data to the variable
            if window:
                # write the data in window chunks
                data_idxs = RasterUtil.get_data_indexes_from_window(window)
                y_start, y_end = data_idxs[0]
                x_start, x_end = data_idxs[1]
                idx = tuple(higher_dim_idxs + [slice(y_start, y_end), slice(x_start, x_end)])
                var[idx] = data
            else:
                idx = tuple(higher_dim_idxs + [Ellipsis])
                var[idx] = data

    @assert_writable
    def add_attribute_to_variable(self, var_name, attr_name, attr_val):
        with self._open():
            var = self.get_variable(var_name)

            setattr(var, attr_name, attr_val)

    @assert_writable
    def add_attribute_to_group(self, group_name, attr_name, attr_val):
        with self._open():
            group = self.get_group(group_name)

            setattr(group, attr_name, attr_val)

    @assert_writable
    def add_global_attribute(self, attr_name, attr_val):
        with self._open() as ds:
            setattr(ds, attr_name, attr_val)

    @timing.timeit
    @assert_writable
    def create_from_data_file(self, data_file, scheme):
        if not isinstance(data_file, FileFormat):
            raise ValueError(f'data_file is not of a subclass of {FileFormat.__module__}.FileFormat')

        if data_file.format == FORMAT_HDF4 and scheme == 'MODIS_HDF4_to_NetCDF4':
            LOGGER.debug(
                f'creating from data file {data_file.file_name} '
                f'(format: {data_file.format}) using scheme {scheme}...'
            )

            with self._open(mode='a'):
                with data_file._open() as ds:
                    LOGGER.debug(f'creating the CRS variable {DEFAULT_CRS_VAR}...')
                    modis_proj = spatial.get_projection('modis_sinusoidal')
                    crs_attrs = modis_proj.get_netcdf_attrs()
                    # use GDAL's geotransform as an attribute
                    crs_attrs['GeoTransform'] = data_file.get_geotransform()
                    crs_props = modis_proj.get_crs_properties()
                    self.add_variable(
                        DEFAULT_CRS_VAR, DEFAULT_CRS_VAR_DTYPE)
                    for name, val in crs_attrs.items():
                        self.add_attribute_to_variable(DEFAULT_CRS_VAR, name, val)

                    # create the dimensions and their variables
                    dims = (DEFAULT_TIME_DIMENSION, DEFAULT_YDIM_DIMENSION, DEFAULT_XDIM_DIMENSION, )
                    # create the time dimension, length 1 (single time slice)
                    modis_temporal = temporal.Modis()
                    time_dt = modis_temporal.extract_modis_datetime(data_file.file_name)
                    time_days = modis_temporal.get_days_since_inception(time_dt)
                    time_attrs = modis_temporal.get_netcdf_time_attributes()
                    LOGGER.debug(f'creating dimension and variable {DEFAULT_TIME_DIMENSION}...')
                    self.add_dimension(DEFAULT_TIME_DIMENSION, 1)
                    self.add_variable(
                        DEFAULT_TIME_DIMENSION, DEFAULT_TEMPORAL_DIMENSION_DTYPE,
                        options={**{'dimensions': (DEFAULT_TIME_DIMENSION)}, **DEFAULT_NETCDF4_VARIABLE_OPTIONS})
                    for name, val in time_attrs.items():
                        self.add_attribute_to_variable(DEFAULT_TIME_DIMENSION, name, val)
                    self.add_data_to_variable(
                        DEFAULT_TIME_DIMENSION,
                        np.array([time_days], dtype=DEFAULT_TEMPORAL_DIMENSION_DTYPE))

                    first_sds = data_file.subdatasets[0]
                    with first_sds._open() as sds:
                        width, height = sds.width, sds.height
                        # extract the values of the dimension's var, which are the center pixel lon/lat
                        # of the CRS
                        x_dim_vals = [sds.xy(row=0, col=col)[0] for col in range(0, width)]
                        y_dim_vals = [sds.xy(row=row, col=0)[1] for row in range(0, height)]
                        LOGGER.debug(f'units = {sds.units}')
                        LOGGER.debug(f'crs = {sds.crs}')
                        LOGGER.debug(f'x_dim range = {x_dim_vals[0]} to {x_dim_vals[-1]}, len = {len(x_dim_vals)}')
                        LOGGER.debug(f'y_dim range = {y_dim_vals[0]} to {y_dim_vals[-1]}, len = {len(y_dim_vals)}')

                        LOGGER.debug(f'creating dimension and variable {DEFAULT_YDIM_DIMENSION}...')
                        self.add_dimension(DEFAULT_YDIM_DIMENSION, height)
                        self.add_variable(
                            DEFAULT_YDIM_DIMENSION, DEFAULT_SPATIAL_DIMENSION_DTYPE,
                            options={**{'dimensions': (DEFAULT_YDIM_DIMENSION)}, **DEFAULT_NETCDF4_VARIABLE_OPTIONS})
                        y_dim_attrs = {**DEFAULT_YDIM_ATTRIBUTES, 'units': crs_props['units'],
                                       'standard_name': crs_props['y_dimension_standard_name']}
                        for name, val in y_dim_attrs.items():
                            self.add_attribute_to_variable(DEFAULT_YDIM_DIMENSION, name, val)
                        self.add_data_to_variable(
                            DEFAULT_YDIM_DIMENSION,
                            np.array(y_dim_vals, dtype=DEFAULT_SPATIAL_DIMENSION_DTYPE))

                        LOGGER.debug(f'creating dimension and variable {DEFAULT_XDIM_DIMENSION}...')
                        self.add_dimension(DEFAULT_XDIM_DIMENSION, width)
                        self.add_variable(
                            DEFAULT_XDIM_DIMENSION, DEFAULT_SPATIAL_DIMENSION_DTYPE,
                            options={**{'dimensions': (DEFAULT_XDIM_DIMENSION)}, **DEFAULT_NETCDF4_VARIABLE_OPTIONS})
                        x_dim_attrs = {**DEFAULT_XDIM_ATTRIBUTES, 'units': crs_props['units'],
                                       'standard_name': crs_props['x_dimension_standard_name']}
                        for name, val in x_dim_attrs.items():
                            self.add_attribute_to_variable(DEFAULT_XDIM_DIMENSION, name, val)
                        self.add_data_to_variable(
                            DEFAULT_XDIM_DIMENSION,
                            np.array(x_dim_vals, dtype=DEFAULT_SPATIAL_DIMENSION_DTYPE))

                    # create the data variables
                    for sds in data_file.subdatasets:
                        with sds._open() as sds_ds:
                            var_name = NetCdf4._get_cf_compliant_name(sds.layer_name)
                            LOGGER.debug(f'creating data variable {var_name}...')
                            attrs = {'long_name': var_name, 'grid_mapping': DEFAULT_CRS_VAR,
                                     'coordinates': ' '.join(dims)}
                            var_options = {'dimensions': dims}

                            meta = sds_ds.meta
                            tags = sds_ds.tags()
                            LOGGER.debug(f'meta = {meta}')
                            LOGGER.debug(f'scales = {sds_ds.scales}')
                            LOGGER.debug(f'tags = {tags}')
                            LOGGER.debug(f'checking compliancy of dtype {np.dtype(meta["dtype"])}...')
                            dtype = NetCdf4._ensure_cf_compliant_dtype(np.dtype(meta['dtype']))
                            LOGGER.debug(f'determined dtype {dtype}')
                            src_info = sds.get_src_info()
                            LOGGER.debug(f'src_info = {src_info}')
                            src_dtype, src_fill_value, src_attrs = src_info['dtype'], src_info['fill_value'], src_info['attributes']

                            LOGGER.debug('determining the fill value...')
                            fill_value, data_fill_value_replace = None, None
                            if '_FillValue' in src_attrs and isinstance(src_attrs['_FillValue'], str):
                                # if the original fill value is a string, it is likely NA,
                                # and no fill value will be used
                                LOGGER.warn(
                                    f'original fill value, {src_attrs["_FillValue"]} '
                                    'is NA or otherwise not numeric and cannot be used')
                                fill_value = None
                            else:
                                if 'nodata' in meta:
                                    # ensure the fill value is cast to the same type as the variable dtype
                                    fill_value = RasterUtil.cast_value_by_dtype(meta['nodata'], dtype)
                                    src_fill_value = RasterUtil.cast_value_by_dtype(src_fill_value, dtype)
                                    if src_dtype != dtype and src_fill_value != fill_value:
                                        # if we've a difference between the original dtype and the dtype cast by rasterio,
                                        #   e.g. unsigned type to signed type
                                        # we need to preserve and use the original fill value
                                        LOGGER.debug(f'preserving original fill value {src_fill_value}...')
                                        data_fill_value_replace = {'from': fill_value, 'to': src_fill_value}
                                        fill_value = src_fill_value
                            if fill_value is not None:
                                var_options['fill_value'] = fill_value

                            if sds_ds.units:
                                try:
                                    units = sds_ds.units[0]
                                except IndexError:
                                    units = None
                                if units:
                                    attrs['units'] = units
                                else:
                                    LOGGER.debug('No units data available for this subdataset')
                            if sds_ds.scales:
                                scale_factor = sds_ds.scales[0]
                                if scale_factor != 1:
                                    attrs['scale_factor'] = scale_factor
                                    if 'scale_factor_err' in tags:
                                        attrs['scale_factor_err'] = float(tags['scale_factor_err'])
                            if sds_ds.offsets:
                                add_offset = sds_ds.offsets[0]
                                attrs['add_offset'] = add_offset
                                if 'add_offset_err' in tags:
                                    attrs['add_offset_err'] = float(tags['add_offset_err'])
                            if 'valid_range' in tags:
                                valid_range = [RasterUtil.cast_value_by_dtype(item.strip(), dtype)
                                               for item in tags['valid_range'].split(',')]
                                attrs['valid_min'] = valid_range[0]
                                attrs['valid_max'] = valid_range[1]
                            if 'calibrated_nt' in tags:
                                attrs['calibrated_nt'] = RasterUtil.cast_value_by_dtype(tags['calibrated_nt'], np.dtype('int'))
                            if 'Legend' in tags:
                                attrs['Legend'] = tags['Legend']

                            self.add_variable(
                                var_name, dtype, set_auto_mask_scale=False,
                                options={**var_options, **DEFAULT_NETCDF4_VARIABLE_OPTIONS})
                            LOGGER.debug(f'attrs = {attrs}')
                            for name, val in attrs.items():
                                self.add_attribute_to_variable(var_name, name, val)

                            # add the data to the variable
                            LOGGER.debug(f'adding data to variable {var_name}...')
                            for window, data in sds.data_by_windows(
                                    window_by_max_bytes=DEFAULT_MAX_WINDOW_BYTES):
                                # recast the source data to the target data type
                                data = RasterUtil.recast_array(data, dtype, in_place=True)

                                if data_fill_value_replace:
                                    from_fill_val = data_fill_value_replace['from']
                                    to_fill_val = data_fill_value_replace['to']
                                    LOGGER.debug(
                                        f'replacing fill value {from_fill_val} '
                                        f'with preserved fill value {to_fill_val} ...'
                                    )
                                    data[data == from_fill_val] = to_fill_val

                                LOGGER.debug(f'writing data for window {window}...')
                                self.add_data_to_variable(var_name, data, window=window, higher_dim_idxs=[0])

                    LOGGER.debug('creating global attributes ...')
                    title = os.path.basename(self.file_name)
                    history = (f'Created {util.get_current_datetime()} from HDF4 format '
                               f'source file {os.path.basename(data_file.file_name)}')
                    global_attrs = {'title': title, 'history': history, **DEFAULT_GLOBAL_ATTRIBUTES}
                    # port over any addt'l attrs from the source
                    ds_tags = ds.tags()

                    LOGGER.debug('attempt to construct the DOI link for the product...')
                    doi_tag_auth = 'identifier_product_doi_authority'
                    doi_tag = 'identifier_product_doi'
                    if doi_tag_auth in ds_tags and doi_tag in ds_tags:
                        doi_link = urljoin(ds_tags[doi_tag_auth], ds_tags[doi_tag])
                        LOGGER.debug(f'DOI link is {doi_link}')
                        global_attrs['references'] = doi_link

                    global_attrs = {**global_attrs, **ds_tags}
                    for name, val in global_attrs.items():
                        self.add_global_attribute(name, val)

                    # create group and data variables for the archive, core and struct metadata
                    LOGGER.debug('creating a group and variables to store global metadata...')
                    metadata_group_name = 'global_attributes'
                    self.add_group(metadata_group_name)
                    metadata_vars = {
                        k: v for k, v in data_file.get_attributes().items()
                        if k in ['ArchiveMetadata.0', 'CoreMetadata.0', 'StructMetadata.0']}
                    for name, data in metadata_vars.items():
                        data = np.array(data, dtype='c')
                        # create the dimension
                        dim_name = f'chars_{name}'
                        self.add_dimension(dim_name, data.shape[0], group=metadata_group_name)
                        attrs = {'coordinates': dim_name}

                        # create the variable
                        var_path = f'/{metadata_group_name}/{name}'
                        var_options = {**{'dimensions': dim_name}, **DEFAULT_NETCDF4_VARIABLE_OPTIONS}
                        self.add_variable(var_path, dtype=np.dtype('c'), set_auto_mask_scale=False, options=var_options)
                        for name, val in attrs.items():
                            self.add_attribute_to_variable(var_path, name, val)

                        # add the data
                        self.add_data_to_variable(var_path, data)

        else:
            raise ValueError('file format and/or scheme is not supported for conversion')


class NetCdf4Error(Exception):
    """A general class for issues with NetCDF 4 files (data, etc.)"""
    pass
