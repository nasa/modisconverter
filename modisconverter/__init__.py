"""modisconverter"""
import tempfile
import shutil
from modisconverter.common import log, version, util, timing
from modisconverter.aws import s3
from modisconverter.formats.hdf import Hdf4
from modisconverter.formats.netcdf import NetCdf4

version_info = version.get_current_version()
__version__ = version_info['Version']
__version_date__ = version_info['CreatedDate']
__version_notes__ = version_info['Notes']
LOGGER = log.get_logger()


class ConversionNotSupportedError(Exception):
    pass


class ConversionError(Exception):
    pass


def convert_file(src: str, dest: str):
    '''
    Converts a MODIS data file from HDF4 to NetCDF4 format.

    Args:
        src (str): the path to the source file.
        dest (str): the path to the destination file to be written. If
            it already exists, it will be overwritten.

    Raises:
        (ConversionNotSupportedError): if the source or destination files
            are not supported formats.
        (ConversionError): if any failure occurred during the
            conversion process.
    '''
    # ensure the conversion is supported
    input_errs = []
    try:
        Hdf4.validate_file_ext(src)
    except ValueError as e:
        input_errs.append(str(e))
    try:
        NetCdf4.validate_file_ext(dest)
    except ValueError as e:
        input_errs.append(str(e))
    if input_errs:
        raise ConversionNotSupportedError('. '.join(input_errs))
    timer = timing.Timer()
    timer.start()
    scheme = 'MODIS_HDF4_to_NetCDF4'

    LOGGER.info(f'converting source file {src} to destination file {dest}')
    if scheme == 'MODIS_HDF4_to_NetCDF4':
        tmp_dir = None
        try:
            s3_target = None
            if s3.is_s3_url(src):
                # download the object so that it can be operated upon
                tmp_dir = tempfile.mkdtemp()
                _, _, object_name = s3.parse_s3_url(src)
                s3_src = util.join_and_normalize(tmp_dir, object_name)
                s3.download_file(src, s3_src)
                src = s3_src
            if s3.is_s3_url(dest):
                tmp_dir = tmp_dir if tmp_dir else tempfile.mkdtemp()
                _, _, object_name = s3.parse_s3_url(dest)
                s3_target = dest
                dest = util.join_and_normalize(tmp_dir, object_name)

            # convert the file
            h4 = Hdf4(src)
            h4.convert(scheme, dest)

            if s3_target:
                # upload the converted file as an S3 object
                s3.upload_file(dest, s3_target)

        except Exception as e:
            raise ConversionError(str(e))
        finally:
            if tmp_dir:
                # delete the temporary directory
                shutil.rmtree(tmp_dir)
            timer.end()
            LOGGER.info(f'conversion took {timer.duration} seconds.')
