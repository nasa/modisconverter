import pandas as pd
from unittest import TestCase, main
from unittest.mock import patch
from modisconverter.common import version


class TestVersion(TestCase):
    @patch('os.path.join')
    @patch('os.path.dirname')
    @patch('pandas.read_csv')
    def test_get_versions_from_csv(self, mock_read_csv, mock_dirname, mock_join):
        expected_base_dir, expected_data_dir, expected_file = (
            'dir', 'data', 'versions.csv'
        )
        mock_dirname.return_value = expected_base_dir
        expected_file_path = 'path'
        mock_join.return_value = expected_file_path
        expected_df = 'df'
        mock_read_csv.return_value = expected_df

        actual_df = version._get_versions_from_csv()

        mock_dirname.assert_called_with(version.__file__)
        mock_join.assert_called_with(
            expected_base_dir, expected_data_dir, expected_file
        )
        self.assertEqual(actual_df, expected_df)

    @patch('modisconverter.common.version._get_versions_from_csv')
    def test_get_current_version(self, mock_get_versions_from_csv):
        expected_csv_dict = {
            'Current': [True], 'Version': ['0.0.0']
        }
        expected_df = pd.DataFrame(data=expected_csv_dict)
        mock_get_versions_from_csv.return_value = expected_df
        expected_ver = {
            'Current': expected_csv_dict['Current'][0],
            'Version': expected_csv_dict['Version'][0]
        }

        actual_ver = version.get_current_version()

        mock_get_versions_from_csv.assert_called_with()
        self.assertEqual(actual_ver, expected_ver)

    @patch('modisconverter.common.version._get_versions_from_csv')
    def test_get_current_version_not_found(self, mock_get_versions_from_csv):
        expected_csv_dict = {
            'Current': [False], 'Version': ['0.0.0']
        }
        expected_df = pd.DataFrame(data=expected_csv_dict)
        mock_get_versions_from_csv.return_value = expected_df

        actual_ver = version.get_current_version()

        mock_get_versions_from_csv.assert_called_with()
        self.assertIsNone(actual_ver)

    @patch('modisconverter.common.version._get_versions_from_csv')
    def test_get_version(self, mock_get_versions_from_csv):
        expected_search_ver = '0.0.50'
        expected_csv_dict = {
            'Current': [True], 'Version': ['0.0.0']
        }
        expected_df = pd.DataFrame(data=expected_csv_dict)
        mock_get_versions_from_csv.return_value = expected_df

        actual_ver = version.get_version(expected_search_ver)

        mock_get_versions_from_csv.assert_called_with()
        self.assertIsNone(actual_ver)

    @patch('modisconverter.common.version._get_versions_from_csv')
    def test_get_version_not_found(self, mock_get_versions_from_csv):
        expected_search_ver = '0.0.1'
        expected_csv_dict = {
            'Current': [True, False], 'Version': [expected_search_ver, '0.0.0']
        }
        expected_df = pd.DataFrame(data=expected_csv_dict)
        mock_get_versions_from_csv.return_value = expected_df
        expected_ver = {
            'Current': expected_csv_dict['Current'][0],
            'Version': expected_csv_dict['Version'][0]
        }

        actual_ver = version.get_version(expected_search_ver)

        mock_get_versions_from_csv.assert_called_with()
        self.assertEqual(actual_ver, expected_ver)

    @patch('modisconverter.common.version.get_current_version')
    def test_get_library_identifier(self, mock_get_current_version):
        expected_cur_ver = '0.0.1'
        mock_get_current_version.return_value = {
            'Version': expected_cur_ver
        }
        expected_id = f'modisconverter v{expected_cur_ver}'

        actual_id = version.get_library_identifier()

        mock_get_current_version.assert_called_with()
        self.assertEqual(actual_id, expected_id)


if __name__ == '__main__':
    main()
