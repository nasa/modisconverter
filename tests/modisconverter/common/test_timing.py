from unittest import TestCase, main
from unittest.mock import patch
from modisconverter.common import timing


class TestTiming(TestCase):
    def test_timit(self):
        @timing.timeit
        def f():
            return 1

        self.assertEqual(f(), 1)


class TestTimer(TestCase):
    @patch('time.perf_counter')
    def test_start(self, mock_perf_counter):
        expected_start = 1
        mock_perf_counter.return_value = expected_start

        actual_timer = timing.Timer()
        actual_timer.start()

        mock_perf_counter.assert_called_with()
        self.assertEqual(actual_timer._start, expected_start)

    @patch('time.perf_counter')
    def test_end(self, mock_perf_counter):
        expected_end = 1
        mock_perf_counter.return_value = expected_end

        actual_timer = timing.Timer()
        actual_timer.end()

        mock_perf_counter.assert_called_with()
        self.assertEqual(actual_timer._end, expected_end)

    @patch('time.perf_counter')
    def test_duration(self, mock_perf_counter):
        expected_end, expected_start = 1, 0
        expected_dur = expected_end - expected_start
        mock_perf_counter.side_effect = [expected_start, expected_end]

        actual_timer = timing.Timer()
        actual_timer.start()
        actual_timer.end()

        self.assertEqual(actual_timer.duration, expected_dur)


if __name__ == '__main__':
    main()
