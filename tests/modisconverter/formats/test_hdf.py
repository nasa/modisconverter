from unittest import TestCase, main
from unittest.mock import patch, Mock
from modisconverter.formats import hdf


class TestHdf4(TestCase):
    @patch('modisconverter.formats.hdf.Hdf4._setup')
    @patch('modisconverter.formats.hdf.Hdf4._set_mode')
    @patch('modisconverter.formats.hdf.Hdf4.validate_file_ext')
    def test_init(self, mock_validate_file_ext, mock_set_mode, mock_setup, return_instance=False):
        expected_file_path = '/my/file.hdf'
        actual_inst = hdf.Hdf4(expected_file_path)
        if return_instance:
            return actual_inst

        mock_validate_file_ext.assert_called_with(expected_file_path)
        mock_set_mode.assert_called_with(hdf.DEFAULT_MODE)
        mock_setup.assert_called_with()

    def test_representation(self):
        actual_inst = self.test_init(return_instance=True)

        self.assertIsInstance(str(actual_inst), str)
        self.assertIsInstance(repr(actual_inst), str)

    @patch('modisconverter.formats.hdf.file_has_ext')
    def test_validate_file_ext_bad_ext(self, mock_file_has_ext):
        actual_inst = self.test_init(return_instance=True)
        expected_file_path = '/my/file.bad'
        mock_file_has_ext.return_value = False

        with self.assertRaises(ValueError):
            actual_inst.validate_file_ext(expected_file_path)
        mock_file_has_ext.assert_called_with(expected_file_path, hdf.FORMAT_HDF4_EXT)

    @patch('modisconverter.formats.hdf.file_has_ext')
    def test_validate_file_ext(self, mock_file_has_ext):
        actual_inst = self.test_init(return_instance=True)
        expected_file_path = '/my/file.hdf'
        mock_file_has_ext.return_value = True

        actual_inst.validate_file_ext(expected_file_path)
        mock_file_has_ext.assert_called_with(expected_file_path, hdf.FORMAT_HDF4_EXT)

    def test_set_mode_bad_mode(self):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = 'bad'

        with self.assertRaises(ValueError):
            actual_inst._set_mode(expected_mode)

    @patch('os.path.exists')
    def test_set_mode_no_file(self, mock_exists):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = hdf.MODE_READ
        mock_exists.return_value = False

        with self.assertRaises(hdf.Hdf4Error):
            actual_inst._set_mode(expected_mode)

    @patch('modisconverter.formats.hdf.HdfSubdataset')
    @patch('modisconverter.formats.hdf.Hdf4._open')
    def test_setup(self, mock_open, mock_HdfSubdataset):
        actual_inst = self.test_init(return_instance=True)
        expected_ds = Mock()
        expected_shp, expected_trans, expected_crs = 'shp', None, None
        expected_ds.shape, expected_ds.transform = expected_shp, expected_trans
        expected_ds.crs = expected_crs
        expected_sds_name_1 = 'layer'
        expected_sdses = [expected_sds_name_1]
        expected_ds.subdatasets = expected_sdses
        expected_sds_1 = Mock()
        expected_sds_1.crs = 'crs'
        expected_sds_1.transform = 'trans'
        mock_HdfSubdataset.return_value = expected_sds_1
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst._setup()

        mock_open.assert_called_with()
        mock_HdfSubdataset.assert_called_with(
            expected_sds_name_1, actual_inst.file_name
        )
        self.assertEqual(actual_inst.shape, expected_shp)
        self.assertEqual(actual_inst.subdatasets, [expected_sds_1])
        self.assertEqual(actual_inst.crs, expected_sds_1.crs)
        self.assertEqual(actual_inst.transform, expected_sds_1.transform)

    @patch('modisconverter.formats.hdf.HdfSubdataset')
    @patch('modisconverter.formats.hdf.Hdf4._open')
    def test_get_geotransform(self, mock_open, mock_HdfSubdataset):
        actual_inst = self.test_init(return_instance=True)
        expected_trans = Mock()
        expected_to_gdal = [
            'line1', 'line2'
        ]
        expected_trans.to_gdal = Mock(return_value=expected_to_gdal)
        actual_inst._transform = expected_trans
        expected_geot = ' '.join(expected_to_gdal)

        actual_geot = actual_inst.get_geotransform()

        expected_trans.to_gdal.assert_called_with()
        self.assertEqual(actual_geot, expected_geot)

    def test_open_already_open(self):
        actual_inst = self.test_init(return_instance=True)
        expected_ds = 'ds'
        actual_inst._open_dataset = Mock()
        actual_inst._open_dataset.ds = expected_ds

        with actual_inst._open() as actual_ds:
            self.assertIs(actual_ds, expected_ds)

    @patch('modisconverter.formats.OpenDataset')
    @patch('modisconverter.formats.hdf.open_with_rio')
    def test_open(self, mock_open_with_rio, mock_OpenDataset):
        actual_inst = self.test_init(return_instance=True)
        expected_mode = 'mode'
        actual_inst._mode = expected_mode
        expected_ds = 'ds'
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open_with_rio.return_value = mock_cm
        expected_ods = 'ds'
        mock_OpenDataset.return_value = expected_ods

        with actual_inst._open() as actual_ds:
            mock_open_with_rio.assert_called_with(actual_inst.file_name)
            mock_OpenDataset.assert_called_with(expected_ds, expected_mode)
            self.assertIs(actual_ds, expected_ods)

    @patch('modisconverter.formats.hdf.open_with_pyhdf')
    def test_get_attributes(self, mock_open_with_pyhdf):
        actual_inst = self.test_init(return_instance=True)
        expected_ds = Mock()
        expected_attrs = {'item': 'val'}
        expected_ds.attributes = Mock(return_value=expected_attrs)
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open_with_pyhdf.return_value = mock_cm

        actual_attrs = actual_inst.get_attributes()

        mock_open_with_pyhdf.assert_called_with(actual_inst.file_name)
        self.assertEqual(actual_attrs, expected_attrs)

    @patch('modisconverter.formats.hdf.NetCdf4')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_convert_replace_existing(self, mock_exists, mock_remove, mock_NetCdf4):
        actual_inst = self.test_init(return_instance=True)
        expected_scheme = 'MODIS_HDF4_to_NetCDF4'
        expected_dst = '/my/file.nc'
        expected_repl = True
        mock_exists.return_value = True
        expected_nc4 = Mock()
        expected_nc4.create_from_data_file = Mock()
        mock_NetCdf4.return_value = expected_nc4

        actual_inst.convert(
            expected_scheme, expected_dst, replace=expected_repl
        )

        mock_exists.assert_called_with(expected_dst)
        mock_remove.assert_called_with(expected_dst)
        mock_NetCdf4.assert_called_with(expected_dst, mode='w')
        expected_nc4.create_from_data_file.assert_called_with(actual_inst, expected_scheme)

    @patch('modisconverter.formats.hdf.NetCdf4')
    @patch('os.path.exists')
    def test_convert_no_replace_existing(self, mock_exists, mock_NetCdf4):
        actual_inst = self.test_init(return_instance=True)
        expected_scheme = 'MODIS_HDF4_to_NetCDF4'
        expected_dst = '/my/file.nc'
        expected_repl = False
        mock_exists.return_value = True

        with self.assertRaises(ValueError):
            actual_inst.convert(
                expected_scheme, expected_dst, replace=expected_repl
            )
        mock_exists.assert_called_with(expected_dst)
        mock_NetCdf4.assert_not_called()

    def test_convert_bad_scheme(self):
        actual_inst = self.test_init(return_instance=True)
        expected_scheme = 'bad'
        expected_dst = '/my/file.nc'
        expected_repl = True

        with self.assertRaises(ValueError):
            actual_inst.convert(
                expected_scheme, expected_dst, replace=expected_repl
            )


class TestHdfSubdataset(TestCase):
    @patch('modisconverter.formats.hdf.HdfSubdataset._setup')
    def test_init(self, mock_setup, return_instance=False):
        expected_name = 'layer'
        expected_file_path = '/my/file.hdf'
        actual_inst = hdf.HdfSubdataset(expected_name, expected_file_path)
        if return_instance:
            return actual_inst

        mock_setup.assert_called_with()
        self.assertEqual(actual_inst.name, expected_name)
        self.assertEqual(actual_inst.file_name, expected_file_path)
        self.assertEqual(actual_inst.layer_name, expected_name)

    def test_representation(self):
        actual_inst = self.test_init(return_instance=True)
        actual_inst._crs, actual_inst._shape = Mock(), 'shp'

        self.assertIsInstance(str(actual_inst), str)
        self.assertIsInstance(repr(actual_inst), str)

    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    def test_setup(self, mock_open):
        actual_inst = self.test_init(return_instance=True)
        expected_crs, expected_trans, expected_shp = 'crs', 'trans', (1, 1)
        expected_dtypes = ('int16', )
        expected_ds = Mock()
        expected_ds.crs, expected_ds.transform = expected_crs, expected_trans
        expected_ds.shape, expected_ds.dtypes = expected_shp, expected_dtypes
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_inst._setup()

        mock_open.assert_called_with()
        self.assertEqual(actual_inst.crs, expected_crs)
        self.assertEqual(actual_inst.transform, expected_trans)
        self.assertEqual(actual_inst.shape, expected_shp)
        self.assertEqual(actual_inst.dtype, expected_dtypes[0])

    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    def test_setup_bad_dims(self, mock_open):
        actual_inst = self.test_init(return_instance=True)
        expected_crs, expected_trans, expected_shp = 'crs', 'trans', (1, 1, 1)
        expected_dtypes = ('int16', )
        expected_ds = Mock()
        expected_ds.crs, expected_ds.transform = expected_crs, expected_trans
        expected_ds.shape, expected_ds.dtypes = expected_shp, expected_dtypes
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)

        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        with self.assertRaises(hdf.Hdf4Error):
            actual_inst._setup()
        mock_open.assert_called_with()

    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    def test_setup_bad_bands(self, mock_open):
        actual_inst = self.test_init(return_instance=True)
        expected_crs, expected_trans, expected_shp = 'crs', 'trans', (1, 1)
        expected_dtypes = ('int16', 'int32')
        expected_ds = Mock()
        expected_ds.crs, expected_ds.transform = expected_crs, expected_trans
        expected_ds.shape, expected_ds.dtypes = expected_shp, expected_dtypes
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)

        def exit_f(inst, exc_type, exc_value, traceback):
            raise exc_type(exc_value)
        mock_cm.__exit__ = exit_f
        mock_open.return_value = mock_cm

        with self.assertRaises(hdf.Hdf4Error):
            actual_inst._setup()
        mock_open.assert_called_with()

    def test_get_geotransform(self):
        actual_inst = self.test_init(return_instance=True)
        expected_trans = Mock()
        expected_to_gdal = [
            'line1', 'line2'
        ]
        expected_trans.to_gdal = Mock(return_value=expected_to_gdal)
        actual_inst._transform = expected_trans
        expected_geot = ' '.join(expected_to_gdal)

        actual_geot = actual_inst.get_geotransform()

        expected_trans.to_gdal.assert_called_with()
        self.assertEqual(actual_geot, expected_geot)

    @patch('modisconverter.formats.hdf.open_with_rio')
    def test_open(self, mock_open_with_rio):
        actual_inst = self.test_init(return_instance=True)
        mock_cm = Mock()
        expected_ds = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open_with_rio.return_value = mock_cm

        with actual_inst._open() as actual_ds:
            self.assertIs(actual_ds, expected_ds)
        mock_open_with_rio.assert_called_with(actual_inst.name)

    @patch('modisconverter.formats.RasterUtil.pyhdf_dtype_to_numpy_dtype')
    @patch('modisconverter.formats.hdf.open_with_pyhdf')
    def test_get_src_info(self, mock_open_with_pyhdf, mock_pyhdf_dtype_to_numpy_dtype):
        actual_inst = self.test_init(return_instance=True)
        mock_cm = Mock()
        expected_ds = Mock()
        expected_sds = Mock()
        expected_fill, expected_sds_attrs = 'f', {}
        expected_sds.getfillvalue = Mock(return_value=expected_fill)
        expected_sds.attributes = Mock(return_value=expected_sds_attrs)
        expected_dtype = 'int16'
        expected_info = (None, None, None, expected_dtype)
        expected_sds.info = Mock(return_value=expected_info)
        mock_pyhdf_dtype_to_numpy_dtype.return_value = expected_dtype
        expected_ds.select = Mock(return_value=expected_sds)
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open_with_pyhdf.return_value = mock_cm
        expected_attrs = {
            'dtype': expected_dtype, 'fill_value': expected_fill,
            'attributes': expected_sds_attrs
        }

        actual_attrs = actual_inst.get_src_info()

        mock_open_with_pyhdf.assert_called_with(actual_inst.file_name)
        self.assertEqual(actual_attrs, expected_attrs)

    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    def test_data(self, mock_open):
        actual_inst = self.test_init(return_instance=True)
        actual_inst._default_band_num = 1
        mock_cm = Mock()
        expected_ds = Mock()
        expected_data = 'd'
        expected_ds.read = Mock(return_value=expected_data)
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        actual_data = actual_inst.data()

        mock_open.assert_called_with()
        self.assertEqual(actual_data, expected_data)

    @patch('modisconverter.formats.RasterUtil.generate_windows')
    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    @patch('modisconverter.formats.RasterUtil.calculate_window_shape')
    def test_data_by_windows(self, mock_calculate_window_shape, mock_open, mock_generate_windows):
        actual_inst = self.test_init(return_instance=True)
        actual_inst._shape = (1, 1)
        actual_inst._dtype = 'int16'
        actual_inst._default_band_num = 1
        expected_win_dims = (1, 1)
        expected_win_shp = (1, 1)
        mock_calculate_window_shape.return_value = expected_win_shp

        expected_ds = Mock()
        expected_data = 'd'
        expected_ds.read = Mock(return_value=expected_data)
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        expected_win1 = {}
        expected_gen_wins = [expected_win1]
        mock_generate_windows.return_value = expected_gen_wins

        actual_win, actual_data = list(
            actual_inst.data_by_windows(window_dims=expected_win_dims)
        )[0]

        mock_calculate_window_shape.assert_called_with(
            actual_inst.shape, actual_inst.dtype, window_dims=expected_win_dims,
            window_by_max_bytes=None
        )
        mock_open.assert_called_with()
        mock_generate_windows.assert_called_with(actual_inst.shape, expected_win_shp)
        self.assertEqual(actual_win, expected_win1)
        self.assertEqual(actual_data, expected_data)

    @patch('modisconverter.formats.RasterUtil.generate_windows')
    @patch('modisconverter.formats.hdf.HdfSubdataset._open')
    @patch('modisconverter.formats.RasterUtil.calculate_window_shape')
    def test_data_by_windows_use_partial(self, mock_calculate_window_shape, mock_open, mock_generate_windows):
        actual_inst = self.test_init(return_instance=True)
        actual_inst._shape = (1, 1)
        actual_inst._dtype = 'int16'
        actual_inst._default_band_num = 1
        expected_win_dims = (1, 1)
        expected_win_shp = (1, 1)
        mock_calculate_window_shape.return_value = expected_win_shp

        expected_ds = Mock()
        expected_data = 'd'
        expected_ds.read = Mock(return_value=expected_data)
        mock_cm = Mock()
        mock_cm.__enter__ = Mock(return_value=expected_ds)
        mock_cm.__exit__ = Mock()
        mock_open.return_value = mock_cm

        expected_win1 = {}
        expected_gen_wins = [expected_win1]
        mock_generate_windows.return_value = expected_gen_wins

        actual_win, actual_data = list(
            actual_inst.data_by_windows(
                window_dims=expected_win_dims,
                data_as_partial=True
            )
        )[0]

        mock_calculate_window_shape.assert_called_with(
            actual_inst.shape, actual_inst.dtype, window_dims=expected_win_dims,
            window_by_max_bytes=None
        )
        mock_open.assert_called_with()
        mock_generate_windows.assert_called_with(actual_inst.shape, expected_win_shp)
        self.assertEqual(actual_win, expected_win1)
        self.assertEqual(actual_data.func, expected_ds.read)
        self.assertEqual(actual_data.args[0], actual_inst._default_band_num)
        self.assertEqual(actual_data.keywords['window'], expected_win1)


if __name__ == '__main__':
    main()
