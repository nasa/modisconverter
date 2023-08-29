from unittest import TestCase, main
from unittest.mock import patch, Mock
import modisconverter as mc
from modisconverter.common import version


class TestPackage(TestCase):
    def test_version(self):
        expected_ver_info = version.get_current_version()
        expected_ver = expected_ver_info['Version']
        expected_date = expected_ver_info['CreatedDate']
        expected_notes = expected_ver_info['Notes']

        self.assertEqual(mc.__version__, expected_ver)
        self.assertEqual(mc.__version_date__, expected_date)
        self.assertEqual(mc.__version_notes__, expected_notes)

    def test_convert_file_bad_files(self):
        with self.assertRaises(mc.ConversionNotSupportedError):
            mc.convert_file('bad', 'more bad')

    @patch('modisconverter.formats.hdf.Hdf4.convert')
    def test_convert_file_conv_failure(self, mock_convert):
        mock_convert.side_effect = RuntimeError('failure')
        with self.assertRaises(mc.ConversionError):
            expected_src, expected_dst = 'file.hdf', 'file.nc'
            mc.convert_file(expected_src, expected_dst)

    @patch('modisconverter.Hdf4')
    def test_convert_file_conv_local_files(self, mock_Hdf4):
        expected_src, expected_dst = 'file.hdf', 'file.nc'
        expected_h4 = Mock()
        expected_h4.convert = Mock()
        mock_Hdf4.return_value = expected_h4
        expected_scheme = 'MODIS_HDF4_to_NetCDF4'

        mc.convert_file(expected_src, expected_dst)

        mock_Hdf4.assert_called_with(expected_src)
        expected_h4.convert.assert_called_with(expected_scheme, expected_dst)

    @patch('modisconverter.common.util.join_and_normalize')
    @patch('modisconverter.aws.s3.upload_file')
    @patch('modisconverter.aws.s3.download_file')
    @patch('modisconverter.aws.s3.parse_s3_url')
    @patch('modisconverter.aws.s3.is_s3_url')
    @patch('modisconverter.Hdf4')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    def test_convert_file_conv_s3_objs(self, mock_mkdtemp, mock_rmtree, mock_Hdf4, mock_is_s3_url, mock_parse_s3_url, mock_download_file, mock_upload_file, mock_join_and_normalize):
        expected_tempdir = '/tmp'
        mock_mkdtemp.return_value = expected_tempdir
        expected_src, expected_dst = 's3://bucket/file.hdf', 's3://bucket/file.nc'
        mock_is_s3_url.return_value = True
        expected_parse_1 = (None, None, 'file.hdf')
        expected_parse_2 = (None, None, 'file.nc')
        mock_parse_s3_url.side_effect = [
            expected_parse_1, expected_parse_2
        ]
        expected_local_1, expected_local_2 = 'file.hdf', 'file.nc'
        mock_join_and_normalize.side_effect = [
            expected_local_1, expected_local_2
        ]
        expected_h4 = Mock()
        expected_h4.convert = Mock()
        mock_Hdf4.return_value = expected_h4
        expected_scheme = 'MODIS_HDF4_to_NetCDF4'

        mc.convert_file(expected_src, expected_dst)

        mock_mkdtemp.assert_called_with()
        mock_is_s3_url.call_args_list[0].asssert_called_with()
        mock_parse_s3_url.call_args_list[0].assert_called_with(expected_src)
        mock_join_and_normalize.call_args_list[0].assert_called_with(expected_tempdir, expected_parse_1[2])
        mock_download_file.assert_called_with(expected_src, expected_local_1)
        mock_is_s3_url.call_args_list[1].asssert_called_with()
        mock_parse_s3_url.call_args_list[1].assert_called_with(expected_dst)
        mock_join_and_normalize.call_args_list[1].assert_called_with(expected_tempdir, expected_parse_2[2])
        mock_upload_file.assert_called_with(expected_local_2, expected_dst)
        mock_Hdf4.assert_called_with(expected_local_1)
        expected_h4.convert.assert_called_with(expected_scheme, expected_local_2)
        mock_rmtree.assert_called_with(expected_tempdir)


if __name__ == '__main__':
    main()
