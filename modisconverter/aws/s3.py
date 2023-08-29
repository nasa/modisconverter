import boto3
from boto3.s3.transfer import TransferConfig
from urllib.parse import urlparse
from modisconverter.common import log, util

LOGGER = log.get_logger()
# a default size of a chunk when downloading/uploading AWS S3 objects
DEFAULT_AWS_S3_CHUNK_BYTES = 1024 * 1024 * 10  # 10 MB


def _get_client():
    return boto3.client('s3')


def is_s3_url(url):
    return True if urlparse(url).scheme == 's3' else False


def parse_s3_url(url):
    parts = urlparse(url)
    if parts.scheme != 's3':
        raise ValueError('url does not use an s3 scheme')

    bucket, key = parts.netloc, parts.path.lstrip('/')
    obj_name = util.split_path(key)[-1]
    return bucket, key, obj_name


def download_file(url, file_path, chunk_bytes=DEFAULT_AWS_S3_CHUNK_BYTES):
    chunk_stmt = f'in chunks of {chunk_bytes} bytes ' if chunk_bytes else ''
    LOGGER.info(f'downloading object {url} as {file_path} {chunk_stmt}...')
    client = _get_client()
    bucket, key, _ = parse_s3_url(url)

    obj = client.get_object(Bucket=bucket, Key=key)
    with open(file_path, 'wb') as f:
        for chunk in iter(lambda: obj['Body'].read(chunk_bytes), b''):
            f.write(chunk)


def upload_file(file_path, url, chunk_bytes=DEFAULT_AWS_S3_CHUNK_BYTES):
    chunk_stmt = f'in chunks of {chunk_bytes} bytes ' if chunk_bytes else ''
    LOGGER.info(f'uploading file {file_path} as {url} {chunk_stmt}...')
    client = _get_client()
    bucket, key, _ = parse_s3_url(url)

    trans_conf = None
    if chunk_bytes:
        trans_conf = TransferConfig(
            multipart_threshold=DEFAULT_AWS_S3_CHUNK_BYTES,
            multipart_chunksize=DEFAULT_AWS_S3_CHUNK_BYTES)
    client.upload_file(file_path, bucket, key, Config=trans_conf)
