import numpy as np
from typing import Callable
from unittest import TestCase, main
from unittest.mock import patch, Mock
from rasterio.windows import Window
from modisconverter.formats import netcdf
from modisconverter.formats import FileFormat, FORMAT_HDF4


class TestNetCdf4(TestCase):
    @patch('modisconverter.formats.netcdf.NetCdf4._setup')
    @patch('modisconverter.formats.netcdf.NetCdf4._set_mode')
    @patch('modisconverter.formats.netcdf.NetCdf4.validate_file_ext')
    def test_init(self, mock_validate_file_ext, mock_set_mode, mock_setup, return_instance=False):
        expected_file_path = '/my/file.nc'
        actual_inst = netcdf.NetCdf4(expected_file_path)
        if return_instance:
            return actual_inst

        mock_validate_file_ext.assert_called_with(expected_file_path)
        mock_set_mode.assert_called_with(netcdf.DEFAULT_MODE)
        mock_setup.assert_called_with()

    @patch('modisconverter.formats.netcdf.file_has_ext')
    def test_validate_file_ext_bad_ext(self, mock_file_has_ext):
        actual_inst = self.test_init(return_instance=True)
        expected_file_path = '/my/file.bad'
        mock_file_has_ext.return_value = False

        with self.assertRaises(ValueError):
            actual_inst.validate_file_ext(expected_file_path)
        mock_file_has_ext.assert_called_with(expected_file_path, netcdf.FORMAT_NETCDF4_EXT)

    @patch('modisconverter.formats.netcdf.file_has_ext')
    def test_validate_file_ext(self, mock_file_has_ext):
        actual_inst = self.test_init(return_instance=True)
        expected_file_path = '/my/file.nc'
        mock_file_has_ext.return_value = True

        actual_inst.validate_file_ext(expected_file_path)
        mock_file_has_ext.assert_called_with(expected_file_path, netcdf.FORMAT_NETCDF4_EXT)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_representation(self, mock_open):
        mock_cm = Mock()
        expected_ds = 'ds'
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_rep = str(actual_inst)

        mock_open.assert_called_with(mode='r')
        self.assertEqual(actual_rep, str(expected_ds))

    def test_set_mode_bad_mode(self):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = 'bad'

        with self.assertRaises(ValueError):
            actual_inst._set_mode(expected_mode)

    @patch('os.path.exists')
    def test_set_mode_no_file(self, mock_exists):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = netcdf.MODE_READ
        mock_exists.return_value = False

        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst._set_mode(expected_mode)

    @patch('os.remove')
    @patch('os.path.exists')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_set_mode_overwrite(self, mock_open, mock_exists, mock_remove):
        mock_cm = Mock()
        expected_ds = 'ds'
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        mock_exists.return_value = True
        expected_mode = netcdf.MODE_WRITE

        actual_inst = self.test_init(return_instance=True)
        actual_inst._set_mode(expected_mode)

        mock_exists.assert_called_with(actual_inst.file_name)
        mock_remove.assert_called_with(actual_inst.file_name)
        mock_open.assert_called_with(mode=expected_mode)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_dimensions(self, mock_open):
        mock_cm = Mock()
        expected_ds = Mock()
        expected_dims = 'd'
        expected_ds.dimensions = expected_dims
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_dims = actual_inst.dimensions

        mock_open.assert_called_with(mode='r')
        self.assertEqual(actual_dims, expected_dims)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_variables(self, mock_open):
        mock_cm = Mock()
        expected_ds = Mock()
        expected_vars = 'v'
        expected_ds.variables = expected_vars
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_vars = actual_inst.variables

        mock_open.assert_called_with(mode='r')
        self.assertEqual(actual_vars, expected_vars)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_groups(self, mock_open):
        mock_cm = Mock()
        expected_ds = Mock()
        expected_groups = 'g'
        expected_ds.groups = expected_groups
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_groups = actual_inst.groups

        mock_open.assert_called_with(mode='r')
        self.assertEqual(actual_groups, expected_groups)

    def test_open_already_open(self):
        actual_inst = self.test_init(return_instance=True)
        expected_ds = 'ds'
        actual_inst._open_dataset = Mock()
        actual_inst._open_dataset.ds = expected_ds

        with actual_inst._open() as actual_ds:
            self.assertIs(actual_ds, expected_ds)

    @patch('modisconverter.formats.OpenDataset')
    @patch('modisconverter.formats.netcdf.open_with_netcdf4')
    def test_open(self, mock_open_with_netcdf4, mock_OpenDataset):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = 'mode'
        actual_inst._mode = expected_mode
        expected_opts = {'format': 'NETCDF4'}
        expected_ds = 'ds'
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open_with_netcdf4.return_value = mock_cm
        expected_ods = 'ds'
        mock_OpenDataset.return_value = expected_ods

        with actual_inst._open() as actual_ds:
            mock_open_with_netcdf4.assert_called_with(
                actual_inst.file_name, mode=expected_mode,
                options=expected_opts
            )
            mock_OpenDataset.assert_called_with(expected_ds, expected_mode)
            self.assertIs(actual_ds, expected_ods)

    @patch('modisconverter.common.util.split_path')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_variable(self, mock_open, mock_split_path):
        expected_name = '/my/var'
        expected_parts = ['my', 'var']
        mock_split_path.return_value = expected_parts
        mock_cm = Mock()
        expected_ds = Mock()
        expected_found_ds = 'found'
        expected_grp = Mock()
        expected_grp.variables = {expected_parts[1]: expected_found_ds}
        expected_ds.groups = {expected_parts[0]: expected_grp}
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_found_ds = actual_inst.get_variable(expected_name)

        mock_open.assert_called_with()
        self.assertEqual(actual_found_ds, expected_found_ds)

    @patch('modisconverter.common.util.split_path')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_variable_not_found(self, mock_open, mock_split_path):
        expected_name = '/my/var'
        expected_parts = ['my', 'var']
        mock_split_path.return_value = expected_parts
        mock_cm = Mock()
        expected_ds = Mock()
        expected_found_ds = 'found'
        expected_grp = Mock()
        expected_grp.variables = {'something': expected_found_ds}
        expected_ds.groups = {expected_parts[0]: expected_grp}
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_found_ds = actual_inst.get_variable(expected_name)

        mock_open.assert_called_with()
        self.assertEqual(actual_found_ds, None)

    @patch('modisconverter.common.util.split_path')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_group(self, mock_open, mock_split_path):
        expected_name = '/my/grp'
        expected_parts = ['my', 'grp']
        mock_split_path.return_value = expected_parts
        mock_cm = Mock()
        expected_ds = Mock()
        expected_found_grp = 'found'
        expected_grp = Mock()
        expected_grp.groups = {expected_parts[1]: expected_found_grp}
        expected_ds.groups = {expected_parts[0]: expected_grp}
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_found_grp = actual_inst.get_group(expected_name)

        mock_open.assert_called_with()
        self.assertEqual(actual_found_grp, expected_found_grp)

    @patch('modisconverter.common.util.split_path')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_group_not_found(self, mock_open, mock_split_path):
        expected_name = '/my/grp'
        expected_parts = ['my', 'grp']
        mock_split_path.return_value = expected_parts
        mock_cm = Mock()
        expected_ds = Mock()
        expected_found_grp = 'found'
        expected_grp = Mock()
        expected_grp.groups = {'something': expected_found_grp}
        expected_ds.groups = {expected_parts[0]: expected_grp}
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_found_grp = actual_inst.get_group(expected_name)

        mock_open.assert_called_with()
        self.assertEqual(actual_found_grp, None)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_variable_data(self, mock_open, mock_get_variable):
        expected_name = '/my/var'
        expected_var = np.array([0])
        mock_get_variable.return_value = expected_var
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=None)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_data = actual_inst.get_variable_data(expected_name)

        mock_open.assert_called_with()
        mock_get_variable.assert_called_with(expected_name)
        self.assertEqual(actual_data, expected_var[:])

    @patch('modisconverter.formats.RasterUtil.get_data_indexes_from_window')
    @patch('modisconverter.formats.RasterUtil.generate_windows')
    @patch('modisconverter.formats.RasterUtil.calculate_window_shape')
    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_variable_data_by_windows(
        self, mock_open, mock_get_variable, mock_calculate_window_shape,
        mock_generate_windows, mock_get_data_indexes_from_window
    ):
        expected_name = '/my/var'
        expected_max_bytes = 10
        expected_var = Mock()
        expected_shp, expected_dt = 'shp', 'dtype'
        expected_var.shape, expected_var.dtype = expected_shp, expected_dt
        expected_data_1 = 'data'
        expected_var.__getitem__ = Mock(return_value=expected_data_1)
        mock_get_variable.return_value = expected_var
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=None)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        expected_win_shp = 'shp'
        mock_calculate_window_shape.return_value = expected_win_shp
        expected_win_1 = 'win'
        expected_wins = [expected_win_1]
        mock_generate_windows.return_value = expected_wins
        expected_data_idx = [
            (0, 1), (0, 1)
        ]
        mock_get_data_indexes_from_window.return_value = expected_data_idx
        expected_items_1 = expected_win_1, expected_data_1

        actual_inst = self.test_init(return_instance=True)
        expected_items = list(
            actual_inst.get_variable_data_by_windows(
                expected_name, window_by_max_bytes=expected_max_bytes
            )
        )
        self.assertEqual(expected_items[0], expected_items_1)

    @patch('modisconverter.formats.RasterUtil.get_data_indexes_from_window')
    @patch('modisconverter.formats.RasterUtil.generate_windows')
    @patch('modisconverter.formats.RasterUtil.calculate_window_shape')
    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_get_variable_data_by_windows_use_partial(
        self, mock_open, mock_get_variable, mock_calculate_window_shape,
        mock_generate_windows, mock_get_data_indexes_from_window
    ):
        expected_name = '/my/var'
        expected_max_bytes = 10
        expected_var = Mock()
        expected_shp, expected_dt = 'shp', 'dtype'
        expected_var.shape, expected_var.dtype = expected_shp, expected_dt
        expected_data_1 = 'data'
        expected_var.__getitem__ = Mock(return_value=expected_data_1)
        mock_get_variable.return_value = expected_var
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=None)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        expected_win_shp = 'shp'
        mock_calculate_window_shape.return_value = expected_win_shp
        expected_win_1 = 'win'
        expected_wins = [expected_win_1]
        mock_generate_windows.return_value = expected_wins
        expected_data_idx = [
            (0, 1), (0, 1)
        ]
        mock_get_data_indexes_from_window.return_value = expected_data_idx
        expected_items_1 = expected_win_1, expected_data_1

        actual_inst = self.test_init(return_instance=True)
        expected_items = list(
            actual_inst.get_variable_data_by_windows(
                expected_name, window_by_max_bytes=expected_max_bytes,
                data_as_partial=True
            )
        )
        actual_win = expected_items[0][0]
        actual_partial = expected_items[0][1]
        self.assertEqual(actual_win, expected_win_1)
        self.assertIsInstance(actual_partial, Callable)
        self.assertEqual(
            actual_partial.args, (
                expected_var, expected_data_idx[0][0], expected_data_idx[0][1],
                expected_data_idx[1][0], expected_data_idx[1][1]
            )
        )

    @patch('modisconverter.formats.netcdf.NetCdf4.get_group')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_dimension_for_group(self, mock_open, mock_get_group):
        expected_name, expected_len = 'name', 10
        expected_grp_name = 'grp'
        expected_grp = Mock()
        expected_grp.dimensions = []
        expected_grp.createDimension = Mock()
        mock_get_group.return_value = expected_grp
        mock_cm = Mock()
        expected_ds = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_dimension(expected_name, expected_len, group=expected_grp_name)

        mock_open.assert_called_with()
        mock_get_group.assert_called_with(expected_grp_name)
        expected_grp.createDimension.assert_called_with(expected_name, expected_len)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_group')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_dimension_creation(self, mock_open, mock_get_group):
        expected_name, expected_len = 'name', 10
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.dimensions = []
        expected_ds.createDimension = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_dimension(expected_name, expected_len)

        mock_open.assert_called_with()
        mock_get_group.assert_not_called()
        expected_ds.createDimension.assert_called_with(expected_name, expected_len)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_group')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_dimension_creation_failure(self, mock_open, mock_get_group):
        expected_name, expected_len = 'name', 10
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.dimensions = []
        expected_ds.createDimension = Mock(side_effect=Exception('failure'))
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE

        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_dimension(expected_name, expected_len)
        mock_open.assert_called_with()
        mock_get_group.assert_not_called()
        expected_ds.createDimension.assert_called_with(expected_name, expected_len)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_group')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_dimension_creation_dim_exists(self, mock_open, mock_get_group):
        expected_name, expected_len = 'name', 10
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.dimensions = [expected_name]
        expected_ds.createDimension = Mock(side_effect=Exception('failure'))
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE

        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_dimension(expected_name, expected_len)
        mock_open.assert_called_with()
        mock_get_group.assert_not_called()
        expected_ds.createDimension.assert_not_called()

    def test_get_cf_compliant_name(self):
        expected_name = 'a&b'
        expected_comp_name = 'a_b'

        actual_inst = self.test_init(return_instance=True)
        self.assertEqual(
            actual_inst._get_cf_compliant_name(expected_name),
            expected_comp_name
        )

    def test_ensure_cf_compliant_dtype(self):
        expected_in_and_out = [
            (np.uint8, np.dtype(np.int16)),
            (np.uint16, np.dtype(np.int32)),
            (np.uint32, np.dtype(np.int64))
        ]
        actual_inst = self.test_init(return_instance=True)

        for i, o in expected_in_and_out:
            self.assertEqual(
                actual_inst._ensure_cf_compliant_dtype(i), o
            )

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_variable_auto_scale(self, mock_open, mock_get_variable):
        expected_name, expected_dtype = 'name', 'int16'
        expected_scale = 'scl'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_var = Mock()
        expected_var.set_auto_maskandscale = Mock()
        expected_ds.createVariable = Mock(return_value=expected_var)
        expected_ds.set_auto_maskandscale = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        mock_get_variable.side_effect = netcdf.NetCdf4Error('does not exist')

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_variable(
            expected_name, expected_dtype, set_auto_mask_scale=expected_scale
        )

        mock_open.assert_called_with()
        mock_get_variable.assert_called_with(expected_name)
        expected_ds.createVariable.assert_called_with(
            expected_name, expected_dtype, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
        )
        expected_var.set_auto_maskandscale.assert_called_with(expected_scale)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_variable_creation_failure(self, mock_open, mock_get_variable):
        expected_name, expected_dtype = 'name', 'int16'
        expected_scale = 'scl'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_var = Mock()
        expected_var.set_auto_maskandscale = Mock()
        expected_ds.createVariable = Mock(side_effect=Exception('failure'))
        expected_ds.set_auto_maskandscale = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm
        mock_get_variable.side_effect = netcdf.NetCdf4Error('does not exist')

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_variable(
                expected_name, expected_dtype, set_auto_mask_scale=expected_scale
            )
        mock_open.assert_called_with()
        mock_get_variable.assert_called_with(expected_name)
        expected_ds.createVariable.assert_called_with(
            expected_name, expected_dtype, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
        )
        expected_var.set_auto_maskandscale.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_variable_already_exists(self, mock_open, mock_get_variable):
        expected_name, expected_dtype = 'name', 'int16'
        expected_scale = 'scl'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_var = Mock()
        expected_ds.createVariable = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm
        mock_get_variable.return_value = expected_var

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_variable(
                expected_name, expected_dtype, set_auto_mask_scale=expected_scale
            )
        mock_open.assert_called_with()
        mock_get_variable.assert_called_with(expected_name)
        expected_ds.createVariable.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_group(self, mock_open):
        expected_name = 'name'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.groups = []
        expected_ds.createGroup = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_group(expected_name)
        
        mock_open.assert_called_with()
        expected_ds.createGroup.assert_called_with(expected_name)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_group_already_exists(self, mock_open):
        expected_name = 'name'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.groups = [expected_name]
        expected_ds.createGroup = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_group(expected_name)
        
        mock_open.assert_called_with()
        expected_ds.createGroup.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_group_creation_failure(self, mock_open):
        expected_name = 'name'
        mock_cm = Mock()
        expected_ds = Mock()
        expected_ds.groups = []
        expected_ds.createGroup = Mock(side_effect=Exception('failure'))
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(netcdf.NetCdf4Error):
            actual_inst.add_group(expected_name)
        
        mock_open.assert_called_with()
        expected_ds.createGroup.assert_called_with(expected_name)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_data_to_variable(self, mock_open, mock_get_variable):
        expected_name = 'var'
        expected_data = np.array([1])
        expected_higher_idxs = [0]
        mock_cm = Mock()
        mock_cm.__enter__ = Mock()
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        expected_var = {}
        mock_get_variable.return_value = expected_var
        expected_var_idx = tuple(expected_higher_idxs + [Ellipsis])
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_data_to_variable(
            expected_name, expected_data, higher_dim_idxs=expected_higher_idxs
        )

        mock_open.assert_called_with()
        self.assertEqual(expected_var, {expected_var_idx: expected_data})

    @patch('modisconverter.formats.RasterUtil.get_data_indexes_from_window')
    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_data_to_variable_using_window(
        self, mock_open, mock_get_variable,
        mock_get_data_indexes_from_window
    ):
        expected_name = 'var'
        expected_data = np.array([1])
        expected_higher_idxs = None
        expected_win = Window(0, 0, 1, 1)
        mock_cm = Mock()
        mock_cm.__enter__ = Mock()
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        expected_var = MockVariable()
        mock_get_variable.return_value = expected_var
        expected_var_idx = '(slice(0, 1, None), slice(0, 1, None))'
        expected_data_idxs = [(0, 1), (0, 1)]
        mock_get_data_indexes_from_window.return_value = expected_data_idxs
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_data_to_variable(
            expected_name, expected_data, higher_dim_idxs=expected_higher_idxs,
            window=expected_win
        )

        mock_open.assert_called_with()
        mock_get_data_indexes_from_window.assert_called_with(
            expected_win
        )
        self.assertEqual(expected_var[expected_var_idx], expected_data)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_data_to_variable_bad_data(self, mock_open):
        expected_name = 'var'
        expected_data = 'bad'
        expected_higher_idxs = None
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(ValueError):
            actual_inst.add_data_to_variable(
                expected_name, expected_data, higher_dim_idxs=expected_higher_idxs
            )
        mock_open.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_data_to_variable_bad_window(self, mock_open):
        expected_name = 'var'
        expected_data = np.array([1])
        expected_win = 'bad'
        expected_higher_idxs = None
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        with self.assertRaises(ValueError):
            actual_inst.add_data_to_variable(
                expected_name, expected_data, higher_dim_idxs=expected_higher_idxs,
                window=expected_win
            )
        mock_open.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4.get_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_attribute_to_variable(self, mock_open, mock_get_variable):
        expected_varname = 'var'
        expected_aname, expected_aval = 'key', 'val'
        expected_var = MockVariable()
        mock_get_variable.return_value = expected_var
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_attribute_to_variable(
            expected_varname, expected_aname, expected_aval
        )

        mock_open.assert_called_with()
        self.assertEqual(getattr(expected_var, expected_aname), expected_aval)

    @patch('modisconverter.formats.netcdf.NetCdf4.get_group')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_attribute_to_group(self, mock_open, mock_get_group):
        expected_groupname = 'var'
        expected_aname, expected_aval = 'key', 'val'
        expected_group = MockVariable()
        mock_get_group.return_value = expected_group
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_attribute_to_group(
            expected_groupname, expected_aname, expected_aval
        )

        mock_open.assert_called_with()
        self.assertEqual(getattr(expected_group, expected_aname), expected_aval)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_add_global_attribute(self, mock_open):
        expected_groupname = 'var'
        expected_aname, expected_aval = 'key', 'val'
        mock_cm = Mock()
        expected_ds = MockVariable()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm
        
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE
        actual_inst.add_global_attribute(
            expected_aname, expected_aval
        )

        mock_open.assert_called_with()
        self.assertEqual(getattr(expected_ds, expected_aname), expected_aval)

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_create_from_data_file_bad_scheme(self, mock_open):
        expected_datafile = Mock(spec=FileFormat)
        expected_scheme = 'bad'

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE

        with self.assertRaises(ValueError) as e_ctx:
            actual_inst.create_from_data_file(
                expected_datafile, expected_scheme
            )
        self.assertTrue('file format and/or scheme is not supported for conversion' in str(e_ctx.exception))
        mock_open.assert_not_called()

    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_create_from_data_file_bad_data_file(self, mock_open):
        expected_datafile = 'bad'
        expected_scheme = 'MODIS_HDF4_to_NetCDF4'
        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE

        with self.assertRaises(ValueError) as e_ctx:
            actual_inst.create_from_data_file(
                expected_datafile, expected_scheme
            )
        self.assertTrue('data_file is not of a subclass of' in str(e_ctx.exception))
        mock_open.assert_not_called()

    @patch('modisconverter.geo.temporal.Modis.get_netcdf_time_attributes')
    @patch('modisconverter.geo.temporal.Modis.get_days_since_inception')
    @patch('modisconverter.geo.temporal.Modis.extract_modis_datetime')
    @patch('modisconverter.formats.netcdf.NetCdf4.add_data_to_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4.add_attribute_to_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4.add_dimension')
    @patch('modisconverter.formats.netcdf.NetCdf4.add_variable')
    @patch('modisconverter.formats.netcdf.NetCdf4._open')
    def test_create_from_data_file(
        self, mock_open, mock_add_variable, mock_add_dimension, mock_add_attribute_to_variable, mock_add_data_to_variable, mock_extract_modis_datetime,
        mock_get_days_since_inception, mock_get_netcdf_time_attributes
    ):
        expected_datafile = Mock(spec=FileFormat)
        expected_filename = 'file.hdf'
        expected_datafile.file_name = expected_filename
        expected_datafile.format = FORMAT_HDF4
        expected_df_metadata = {
            'ArchiveMetadata.0': 'val'
        }
        expected_datafile.get_attributes = Mock(return_value=expected_df_metadata)
        expected_geotrans = 'gt'
        expected_datafile.get_geotransform = Mock(return_value=expected_geotrans)
        expected_sds_1 = Mock()
        expected_sds_1_ds = Mock()
        expected_sds_1_ds.width, expected_sds_1_ds.height = 1, 1
        expected_src_info = {
            'dtype': 'int16', 'fill_value': 1, 'attributes': {}
        }
        expected_sds_1.get_src_info = Mock(return_value=expected_src_info)

        expected_sds_1_ds.xy = Mock(side_effect=[
            (0, 0), (0, 0)
        ])
        expected_sds_1_ds.meta = {
            'dtype': 'int16', 'nodata': expected_src_info['fill_value']
        }
        expected_sds_1_ds.tags = Mock(return_value={
            'scale_factor_err': '0',
            'add_offset_err': '0',
            'valid_range': '0,1',
            'calibrated_nt': '5',
            'Legend': 'legend',
            'Description': 'desc'
        })
        expected_sds_1_ds.units = ('unit', )
        expected_sds_1_ds.scales = (2.0, )
        expected_sds_1_ds.offsets = (1.0, )
        expected_sds_1.layer_name = 'lyr'
        expected_sds_1.data_by_windows = Mock(return_value=[
            ('win', np.array([1]))
        ])
        mock_cm_sds1 = Mock()
        mock_cm_sds1.__enter__ = Mock(return_value=expected_sds_1_ds)
        mock_cm_sds1.__exit__ = Mock()
        expected_sds_1._open = Mock(return_value=mock_cm_sds1)
        expected_subs = [
            expected_sds_1
        ]
        expected_datafile.subdatasets = expected_subs

        expected_time_dt = 'dt'
        expected_time_days = 1
        expected_time_attrs = {}
        mock_extract_modis_datetime.return_value = expected_time_dt
        mock_get_days_since_inception.return_value = expected_time_days
        mock_get_netcdf_time_attributes.return_value = expected_time_attrs

        expected_scheme = 'MODIS_HDF4_to_NetCDF4'
        mock_cm = Mock()
        expected_ds = MockVariable()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        expected_datafile._open = Mock(return_value=mock_cm)
        expected_tags = {
            'identifier_product_doi_authority': 'a',
            'identifier_product_doi': 'd'
        }
        expected_ds.tags = Mock(return_value=expected_tags)

        actual_inst = self.test_init(return_instance=True)
        actual_inst._mode = netcdf.MODE_WRITE

        actual_inst.create_from_data_file(
            expected_datafile, expected_scheme
        )
        
        mock_open.call_args_list[0].assert_called_with(mode='a')
        expected_datafile._open.assert_called_with()
        print(mock_add_variable.call_args_list)
        mock_add_variable.call_args_list[0].assert_called_with(
            netcdf.DEFAULT_CRS_VAR, netcdf.DEFAULT_CRS_VAR_DTYPE
        )
        mock_add_variable.call_args_list[1].assert_called_with(
            netcdf.DEFAULT_TIME_DIMENSION, netcdf.DEFAULT_TEMPORAL_DIMENSION_DTYPE,
            options={
                **{'dimensions': (netcdf.DEFAULT_TIME_DIMENSION)}, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
            }
        )
        mock_add_variable.call_args_list[2].assert_called_with(
            netcdf.DEFAULT_YDIM_DIMENSION, netcdf.DEFAULT_SPATIAL_DIMENSION_DTYPE,
            options={
                **{'dimensions': (netcdf.DEFAULT_YDIM_DIMENSION)}, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
            }
        )
        mock_add_variable.call_args_list[3].assert_called_with(
            netcdf.DEFAULT_XDIM_DIMENSION, netcdf.DEFAULT_SPATIAL_DIMENSION_DTYPE,
            options={
                **{'dimensions': (netcdf.DEFAULT_XDIM_DIMENSION)}, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
            }
        )
        mock_add_variable.call_args_list[4].assert_called_with(
            expected_sds_1.layer_name, np.dtype(expected_src_info['dtype']), set_auto_mask_scale=False,
            options={
                **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
            }
        )
        mock_add_variable.call_args_list[5].assert_called_with(
            '/global_attributes/ArchiveMetadata.0', dtype=np.dtype('c'), set_auto_mask_scale=False, options={
                **{'dimensions': 'chars_ArchiveMetadata.0'}, **netcdf.DEFAULT_NETCDF4_VARIABLE_OPTIONS
            }
        )


class MockVariable(dict):
    def __init__(self, d=None):
        if d is None:
            d = {}
        self._data = d

    def __setitem__(self, k, v):
        k = str(k)
        self._data[k] = v

    def __getitem__(self, k):
        return self._data[k]

if __name__ == '__main__':
    main()
