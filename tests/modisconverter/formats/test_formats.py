import rasterio as rio
import numpy as np
from unittest import TestCase, main
from unittest.mock import patch, Mock
from modisconverter import formats


class TestPackage(TestCase):
    @patch('rasterio.open')
    def test_open_with_rio(self, mock_open):
        expected_src = 'file'
        expected_mode = 'r'
        expected_opts = {'opt': 'val'}
        expected_reader = Mock()
        expected_reader.closed = False
        mock_open.return_value = expected_reader
        with formats.open_with_rio(expected_src, mode=expected_mode, options=expected_opts):
            mock_open.assert_called_with(
                expected_src, mode=expected_mode, **expected_opts
            )
        expected_reader.close.assert_called_with()

    @patch('rasterio.open')
    def test_open_with_rio_read_error(self, mock_open):
        expected_src = 'file'
        expected_mode = 'r'
        expected_opts = {'opt': 'val'}
        expected_reader = Mock(spec=rio.io.DatasetReader)
        expected_reader.closed = False
        mock_open.side_effect = RuntimeError('read error')
        with self.assertRaises(formats.RasterioReadError):
            with formats.open_with_rio(expected_src, mode=expected_mode, options=expected_opts):
                mock_open.assert_called_with(
                    expected_src, mode=expected_mode, **expected_opts
                )
        expected_reader.close.assert_not_called()

    @patch('netCDF4.Dataset')
    def test_open_with_netcdf4(self, mock_ds):
        expected_src = 'file'
        expected_mode = 'r'
        expected_opts = {'opt': 'val'}
        expected_reader = Mock()
        expected_reader.isopen = True
        mock_ds.return_value = expected_reader
        with formats.open_with_netcdf4(expected_src, mode=expected_mode, options=expected_opts):
            mock_ds.assert_called_with(
                expected_src, mode=expected_mode, **expected_opts
            )
        expected_reader.close.assert_called_with()

    @patch('netCDF4.Dataset')
    def test_open_with_netcdf4_read_error(self, mock_ds):
        expected_src = 'file'
        expected_mode = 'r'
        expected_opts = {'opt': 'val'}
        expected_reader = Mock()
        mock_ds.side_effect = RuntimeError('read fail')
        with self.assertRaises(formats.NetCdf4ReadError):
            with formats.open_with_netcdf4(expected_src, mode=expected_mode, options=expected_opts):
                mock_ds.assert_called_with(
                    expected_src, mode=expected_mode, **expected_opts
                )
        expected_reader.close.assert_not_called()

    @patch('modisconverter.formats.HdfSd')
    def test_open_with_pyhdf(self, mock_sd):
        expected_src = 'file'
        expected_reader = Mock()
        expected_reader.end = Mock()
        mock_sd.return_value = expected_reader
        with formats.open_with_pyhdf(expected_src):
            mock_sd.assert_called_with(expected_src)
        expected_reader.end.assert_called_with()

    @patch('modisconverter.formats.HdfSd')
    def test_open_with_pyhdf_read_error(self, mock_sd):
        expected_src = 'file'
        expected_reader = Mock()
        expected_reader.end = Mock()
        mock_sd.side_effect = RuntimeError('read fail')
        with self.assertRaises(formats.NetCdf4ReadError):
            with formats.open_with_pyhdf(expected_src):
                mock_sd.assert_called_with(expected_src)
        expected_reader.end.assert_not_called()

    def test_file_has_ext(self):
        expected_fp = 'file.nc'

        self.assertTrue(formats.file_has_ext(expected_fp, 'nc'))
        self.assertFalse(formats.file_has_ext(expected_fp, 'txt'))


class TestRasterUtil(TestCase):
    def test_generate_windows(self):
        expected_data_shp = (2, 2)
        expected_window_shp = (1, 1)
        expected_windows = [
            rio.windows.Window(col_off=0, row_off=0, width=1, height=1),
            rio.windows.Window(col_off=1, row_off=0, width=1, height=1),
            rio.windows.Window(col_off=0, row_off=1, width=1, height=1),
            rio.windows.Window(col_off=1, row_off=1, width=1, height=1)
        ]

        actual_windows = list(formats.RasterUtil.generate_windows(
            expected_data_shp, expected_window_shp
        ))

        self.assertEqual(actual_windows, expected_windows)

    def test_calculate_window_shape_by_max_bytes(self):
        expected_data_shp = (5000, 5000)
        expected_data_type = 'int16'
        expected_max_bytes = (2 ** 10) ** 2 * 2  # 2 MiB
        expected_shp = (1024, 1024)

        actual_shp = formats.RasterUtil.calculate_window_shape(
            expected_data_shp, expected_data_type, window_by_max_bytes=expected_max_bytes
        )

        self.assertEqual(actual_shp, expected_shp)

    def test_calculate_window_shape_by_window_dims(self):
        expected_data_shp = (5000, 5000)
        expected_data_type = 'int16'
        expected_window_dims = (6000, 6000)
        expected_shp = (5000, 5000)

        actual_shp = formats.RasterUtil.calculate_window_shape(
            expected_data_shp, expected_data_type,
            window_dims=expected_window_dims
        )

        self.assertEqual(actual_shp, expected_shp)

    def test_calculate_window_shape_no_choice_present(self):
        expected_data_shp = (5000, 5000)
        expected_data_type = 'int16'

        with self.assertRaises(ValueError):
            formats.RasterUtil.calculate_window_shape(
                expected_data_shp, expected_data_type
            )

    def test_get_data_indexes_from_window(self):
        expected_window = rio.windows.Window(1, 1, 10, 10)
        expected_idxes = ((1, 11), (1, 11))

        actual_idxes = formats.RasterUtil.get_data_indexes_from_window(
            expected_window
        )

        self.assertEqual(actual_idxes, expected_idxes)

    def test_get_data_indexes_from_window_bad_input(self):
        expected_window = Mock()

        with self.assertRaises(ValueError):
            formats.RasterUtil.get_data_indexes_from_window(
                expected_window
            )

    def test_cast_value_by_dtype(self):
        expected_val = 1
        expected_dtype = 'float32'
        expected_cast = np.array(expected_val, dtype=expected_dtype)

        actual_cast = formats.RasterUtil.cast_value_by_dtype(expected_val, expected_dtype)

        self.assertEquals(actual_cast, expected_cast)

    def test_recast_array(self):
        expected_arr = np.array([1])
        expected_dtype = 'float32'
        expected_cast = np.array([1.0], dtype=expected_dtype)

        actual_cast = formats.RasterUtil.recast_array(expected_arr, expected_dtype)

        self.assertEqual(actual_cast, expected_cast)

    def test_recast_array_no_cast_needed(self):
        expected_arr = np.array([1])
        expected_dtype = expected_arr.dtype

        actual_cast = formats.RasterUtil.recast_array(expected_arr, expected_dtype)

        self.assertIs(actual_cast, expected_arr)

    def test_recast_array_cast_failure(self):
        expected_arr = np.array([1])
        expected_dtype = 'string'

        with self.assertRaises(formats.RasterError):
            formats.RasterUtil.recast_array(expected_arr, expected_dtype)

    def test_replace_nan_in_array(self):
        expected_arr = np.array([np.nan])
        expected_re = 1
        expected_repl = np.array([1.0])

        actual_repl = formats.RasterUtil.replace_nan_in_array(
            expected_arr, expected_re
        )

        self.assertEqual(actual_repl, expected_repl)

    def test_replace_nan_in_array_failure(self):
        expected_arr = np.array([np.nan])
        expected_re = complex(1, 3)

        with self.assertRaises(formats.RasterError):
            formats.RasterUtil.replace_nan_in_array(
                expected_arr, expected_re
            )

    def test_pyhdf_dtype_to_numpy_dtype(self):
        expected_id = formats.SDC.UINT16
        expected_dtype = np.dtype('uint16')

        actual_dtype = formats.RasterUtil.pyhdf_dtype_to_numpy_dtype(expected_id)

        self.assertEqual(actual_dtype, expected_dtype)

    def test_pyhdf_dtype_to_numpy_dtype_unknown(self):
        expected_id = 'unknown'
        with self.assertRaises(ValueError):
            formats.RasterUtil.pyhdf_dtype_to_numpy_dtype(expected_id)


if __name__ == '__main__':
    main()
