from datetime import datetime
from unittest import TestCase, main
from unittest.mock import patch, Mock
from modisconverter.geo import temporal


class TestModis(TestCase):
    def test_init(self, return_instance=False):
        actual_inst = temporal.Modis()
        if return_instance:
            return actual_inst

        expected_incept = datetime(2000, 1, 1, 0, 0, 0)
        self.assertEqual(actual_inst.inception, expected_incept)

    def test_get_days_since_inception(self):
        expected_dt = datetime.now()
        actual_inst = self.test_init(return_instance=True)
        expected_days_since = (expected_dt - actual_inst.inception).days

        actual_days_since = actual_inst.get_days_since_inception(expected_dt)

        self.assertEqual(actual_days_since, expected_days_since)

    @patch('modisconverter.common.util.julian_to_datetime')
    @patch('re.search')
    def test_extract_modis_datetime(self, mock_search, mock_julian_to_datetime):
        expected_file_name = 'file'
        actual_inst = self.test_init(return_instance=True)
        expected_ptrn = '\.A(\d{4})(\d{3})\.'
        expected_match = Mock()
        expected_grp_1, expected_grp_2 = '1', '2'
        expected_match.group = Mock(side_effect=[expected_grp_1, expected_grp_2])
        mock_search.return_value = expected_match
        expected_dt = 'dt'
        mock_julian_to_datetime.return_value = expected_dt

        actual_dt = actual_inst.extract_modis_datetime(expected_file_name)

        mock_search.assert_called_with(expected_ptrn, expected_file_name)
        expected_match.group.call_args_list[0].assert_called_with(1)
        expected_match.group.call_args_list[1].assert_called_with(2)
        mock_julian_to_datetime.assert_called_with(expected_grp_1, expected_grp_2)
        self.assertEqual(actual_dt, expected_dt)

    @patch('modisconverter.common.util.julian_to_datetime')
    @patch('re.search')
    def test_extract_modis_datetime_cannot_parse(self, mock_search, mock_julian_to_datetime):
        expected_file_name = 'file'
        actual_inst = self.test_init(return_instance=True)
        expected_ptrn = '\.A(\d{4})(\d{3})\.'
        expected_match = None
        mock_search.return_value = expected_match
        expected_dt = None
        mock_julian_to_datetime.return_value = expected_dt

        actual_dt = actual_inst.extract_modis_datetime(expected_file_name)

        mock_search.assert_called_with(expected_ptrn, expected_file_name)
        mock_julian_to_datetime.assert_not_called()
        self.assertEqual(actual_dt, expected_dt)

    def test_get_netcdf_time_attributes(self):
        actual_inst = self.test_init(return_instance=True)
        expected_attrs = {
            'axis': 'T',
            'calendar': 'julian',
            'units': f'days since {actual_inst.inception.strftime("%Y-%m-%d %H:%M:%S")}',
            'standard_name': 'time'
        }

        actual_attrs = actual_inst.get_netcdf_time_attributes()

        self.assertEqual(actual_attrs, expected_attrs)


if __name__ == '__main__':
    main()
