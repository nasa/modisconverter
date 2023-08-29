from unittest import TestCase, main
from unittest.mock import Mock, patch
from modisconverter.aws import s3


class TestS3(TestCase):
    @patch('boto3.client')
    def test_get_client(self, mock_client):
        """
        Tests getting an S3 client
        """

        s3._get_client()
        mock_client.assert_called_with('s3')

    def test_is_s3_url(self):
        """
        Tests if a URL is for an S3 object
        """

        expected_result = True
        expected_url = 's3://bucket/key'

        actual_result = s3.is_s3_url(expected_url)

        self.assertEqual(actual_result, expected_result)

    def test_is_not_s3_url(self):
        """
        Tests if a URL does not pertain to an S3 object
        """

        expected_result = False
        expected_url = '/some/path'

        actual_result = s3.is_s3_url(expected_url)

        self.assertEqual(actual_result, expected_result)

    def test_parse_s3_url(self):
        """
        Tests parsing an S3 URL into bucket, key, and object name
        """

        expected_bucket = 'bucket'
        expected_obj_name = 'obj'
        expected_key = f'key/{expected_obj_name}'
        expected_url = f's3://{expected_bucket}/{expected_key}'

        actual_bucket, actual_key, actual_obj_name = s3.parse_s3_url(expected_url)

        self.assertEqual(actual_bucket, expected_bucket)
        self.assertEqual(actual_key, expected_key)
        self.assertEqual(actual_obj_name, expected_obj_name)

    def test_parse_s3_url_failure(self):
        """
        Tests failure to parse an S3 URL
        """

        expected_bucket = 'bucket'
        expected_obj_name = 'obj'
        expected_key = f'key/{expected_obj_name}'
        expected_url = f'{expected_bucket}/{expected_key}'

        with self.assertRaises(ValueError):
            s3.parse_s3_url(expected_url)

    @patch('builtins.open')
    @patch('modisconverter.aws.s3.parse_s3_url')
    @patch('modisconverter.aws.s3._get_client')
    def test_download_file(self, mock_get_client, mock_parse_s3_url, mock_open):
        """
        Tests downloading an S3 object to a local file
        """

        expected_bucket = 'an'
        expected_obj_name = 'obj'
        expected_key = f'example/{expected_obj_name}'
        expected_url = f's3://{expected_bucket}/{expected_key}'
        expected_open_mode = 'wb'
        expected_file_path = '/my/file'
        mock_parse_s3_url.return_value = (expected_bucket, expected_key, expected_obj_name)
        expected_read_data = b'data'
        expected_read_returns = [expected_read_data, b'']
        mock_obj_body = Mock()
        mock_obj_body.read = Mock(side_effect=expected_read_returns)
        expected_object = {
            'Body': mock_obj_body
        }
        mock_client = Mock()
        mock_client.get_object = Mock(return_value=expected_object)
        mock_get_client.return_value = mock_client
        mock_file_open = Mock()
        mock_file_obj = Mock()
        mock_file_obj.write = Mock()
        mock_file_open.__enter__ = Mock(return_value=mock_file_obj)
        mock_file_open.__exit__ = Mock()
        mock_open.return_value = mock_file_open

        s3.download_file(expected_url, expected_file_path)

        mock_get_client.assert_called_with()
        mock_parse_s3_url.assert_called_with(expected_url)
        mock_client.get_object.assert_called_with(Bucket=expected_bucket, Key=expected_key)
        mock_open.assert_called_with(expected_file_path, expected_open_mode)
        mock_obj_body.read.call_args_list[0].assert_called_with(s3.DEFAULT_AWS_S3_CHUNK_BYTES)
        mock_obj_body.read.call_args_list[1].assert_called_with(s3.DEFAULT_AWS_S3_CHUNK_BYTES)
        mock_file_obj.write.assert_called_with(expected_read_returns[0])

    @patch('modisconverter.aws.s3.TransferConfig')
    @patch('modisconverter.aws.s3.parse_s3_url')
    @patch('modisconverter.aws.s3._get_client')
    def test_upload_file(self, mock_get_client, mock_parse_s3_url, mock_transport_config):
        """
        Tests uploading a local file to an S3 object
        """

        expected_bucket = 'an'
        expected_obj_name = 'obj'
        expected_key = f'example/{expected_obj_name}'
        expected_url = f's3://{expected_bucket}/{expected_key}'
        expected_file_path = '/my/file'
        mock_parse_s3_url.return_value = (expected_bucket, expected_key, expected_obj_name)

        mock_client = Mock()
        mock_client.upload_file = Mock()
        mock_get_client.return_value = mock_client

        expected_trans_conf = {}
        mock_transport_config.return_value = expected_trans_conf

        s3.upload_file(expected_file_path, expected_url)


if __name__ == '__main__':
    main()
