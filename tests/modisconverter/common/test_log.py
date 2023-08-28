from datetime import datetime
from time import time
from unittest import TestCase, main
from unittest.mock import patch, Mock
from modisconverter.common import log


class TestLog(TestCase):
    @patch('modisconverter.common.log.LogFormatter')
    @patch('logging.StreamHandler')
    @patch('logging.getLogger')
    @patch('logging.root.manager')
    def test_get_logger_new(self, mock_manager, mock_get_logger, mock_stream_handler, mock_log_formatter):
        mock_manager.loggerDict = {}
        expected_handler = Mock()
        expected_handler.setLevel = Mock()
        expected_handler.setFormatter = Mock()
        mock_stream_handler.return_value = expected_handler
        expected_logger = Mock()
        expected_logger.addHandler = Mock()
        expected_logger.setLevel = Mock()
        mock_get_logger.return_value = expected_logger
        expected_formatter = 'f'
        mock_log_formatter.return_value = expected_formatter
        expected_log_level = log.LOG_LEVEL

        actual_logger = log.get_logger()

        mock_stream_handler.assert_called_with()
        expected_handler.setLevel.assert_called_with(expected_log_level)
        expected_handler.setFormatter.assert_called_with(expected_formatter)
        mock_log_formatter.assert_called_with(log.LOG_FORMAT, datefmt=log.LOG_DATE_FORMAT)
        mock_get_logger.assert_called_with(log.LOGGER_NAME)
        expected_logger.addHandler.assert_called_with(expected_handler)
        expected_logger.setLevel.assert_called_with(expected_log_level)
        self.assertEqual(actual_logger, expected_logger)

    @patch('logging.StreamHandler')
    @patch('logging.getLogger')
    @patch('logging.root.manager')
    def test_get_logger_existing(self, mock_manager, mock_get_logger, mock_stream_handler):
        mock_manager.loggerDict = {log.LOGGER_NAME: None}
        expected_logger = 'l'
        mock_get_logger.return_value = expected_logger

        actual_logger = log.get_logger()

        mock_get_logger.assert_called_with(log.LOGGER_NAME)
        mock_stream_handler.assert_not_called()
        self.assertEqual(actual_logger, expected_logger)

    @patch('os.environ.get')
    @patch('modisconverter.common.log.LogFormatter')
    @patch('logging.StreamHandler')
    @patch('logging.getLogger')
    @patch('logging.root.manager')
    def test_get_logger_env_log_level(self, mock_manager, mock_get_logger, mock_stream_handler, mock_log_formatter, mock_get):
        mock_manager.loggerDict = {}
        expected_handler = Mock()
        expected_handler.setLevel = Mock()
        expected_handler.setFormatter = Mock()
        mock_stream_handler.return_value = expected_handler
        expected_logger = Mock()
        expected_logger.addHandler = Mock()
        expected_logger.setLevel = Mock()
        mock_get_logger.return_value = expected_logger
        expected_formatter = 'f'
        mock_log_formatter.return_value = expected_formatter
        expected_env_log_level = '10'
        expected_log_level = int(expected_env_log_level)
        mock_get.return_value = expected_env_log_level

        actual_logger = log.get_logger()

        mock_stream_handler.assert_called_with()
        expected_handler.setLevel.assert_called_with(expected_log_level)
        expected_handler.setFormatter.assert_called_with(expected_formatter)
        mock_log_formatter.assert_called_with(log.LOG_FORMAT, datefmt=log.LOG_DATE_FORMAT)
        mock_get_logger.assert_called_with(log.LOGGER_NAME)
        expected_logger.addHandler.assert_called_with(expected_handler)
        expected_logger.setLevel.assert_called_with(expected_log_level)
        self.assertEqual(actual_logger, expected_logger)


class TestLogFormatter(TestCase):
    def test_formatTime_with_fmt(self):
        actual_fmter = log.LogFormatter(
            log.LOG_FORMAT, datefmt=log.LOG_DATE_FORMAT
        )
        expected_record = Mock()
        expected_created = time()
        expected_t = actual_fmter.converter(
            expected_created
        ).replace(tzinfo=log.tzlocal()).strftime(
            log.LOG_DATE_FORMAT
        )
        expected_record.created = expected_created

        actual_t = actual_fmter.formatTime(expected_record, datefmt=log.LOG_DATE_FORMAT)

        self.assertEqual(actual_t, expected_t)

    def test_formatTime_without_fmt(self):
        expected_fmt = '%Y-%m-%d %H:%M:%S'
        actual_fmter = log.LogFormatter(
            log.LOG_FORMAT
        )
        expected_record = Mock()
        expected_created = time()
        expected_t = actual_fmter.converter(
            expected_created
        ).replace(tzinfo=log.tzlocal()).strftime(
            expected_fmt
        )
        expected_record.created = expected_created
        expected_msecs = 0
        expected_record.msecs = expected_msecs
        expected_t = f'{expected_t},000'

        actual_t = actual_fmter.formatTime(expected_record)

        self.assertEqual(actual_t, expected_t)



if __name__ == '__main__':
    main()
