from unittest import TestCase, main
from unittest.mock import patch, Mock
from modisconverter.common import util


class TestUtil(TestCase):
    @patch('os.path.join')
    @patch('os.path.normpath')
    def test_join_and_normalize(self, mock_normpath, mock_join):
        expected_dir, expected_file = 'dir', 'file'
        expected_join = 'join'
        mock_join.return_value = expected_join
        expected_norm = 'norm'
        mock_normpath.return_value = expected_norm

        actual_norm = util.join_and_normalize(expected_dir, expected_file)

        mock_join.assert_called_with(expected_dir, expected_file)
        mock_normpath.assert_called_with(expected_join)
        self.assertEqual(actual_norm, expected_norm)

    def test_split_path(self):
        expected_path = '/some/path'
        expected_split = ['some', 'path']

        actual_split = util.split_path(expected_path)

        self.assertEqual(actual_split, expected_split)

    @patch('modisconverter.common.util.datetime')
    def test_get_current_datetime(self, mock_datetime):
        expected_tz, expected_fmt = 'tz', 'fm'
        expected_cur_dt = 'dt'
        expected_now_dt = Mock()
        expected_now_dt.strftime = Mock(return_value=expected_cur_dt)
        mock_datetime.now = Mock(return_value=expected_now_dt)

        actual_cur_dt = util.get_current_datetime(
            tz=expected_tz, format=expected_fmt
        )

        mock_datetime.now.assert_called_with(expected_tz)
        expected_now_dt.strftime.assert_called_with(expected_fmt)
        self.assertEqual(actual_cur_dt, expected_cur_dt)

    @patch('modisconverter.common.util.datetime')
    def test_julian_to_datetime(self, mock_datetime):
        expected_yr, expected_doy = 'y', 'doy'
        expected_dt = 'dt'
        mock_datetime.strptime = Mock(return_value=expected_dt)

        actual_dt = util.julian_to_datetime(expected_yr, expected_doy)

        mock_datetime.strptime.assert_called_with(
            f'{expected_yr}{expected_doy}', '%Y%j'
        )
        self.assertEqual(actual_dt, expected_dt)


if __name__ == '__main__':
    main()
