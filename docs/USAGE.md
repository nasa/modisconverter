# Usage

## Converting a MODIS granule using local files

```python
from modisconverter import convert_file

src = 'MOD13Q1.A2004353.h02v11.061.2020213145209.hdf'
dst = 'MOD13Q1.A2004353.h02v11.061.2020213145209.nc'
convert_file(src, dst)
2023-08-16 15:58:35.678425 +0000        INFO    converting source file MOD13Q1.A2004353.h02v11.061.2020213145209.hdf to destination file MOD13Q1.A2004353.h02v11.061.2020213145209.nc
...
2023-08-16 15:58:51.213085 +0000        INFO    conversion took 15.534909838985186 seconds.
```

## Converting a MODIS granule using AWS S3 objects

Source and destination [AWS S3](https://aws.amazon.com/s3/) objects are supported in conversion.  If the source is an S3 object, it is downloaded first and then converted.  If the destination is an S3 object, the converted file is uploaded as that object.

Ensure that your environment uses [AWS credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) so that the AWS Python SDK can download or upload objects to your specified bucket(s).  For example, if you've a configured AWS profile, you can set the `AWS_PROFILE` environment variable to that profile.

```bash
# set the profile so that interaction with the S3 bucket works
export AWS_PROFILE=my-profile
```

```python
from modisconverter import convert_file

src = 's3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.hdf'
dst = 's3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.nc'
convert_file(src, dst)

2023-08-16 16:25:06.832608 +0000        INFO    converting source file s3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.hdf to destination file s3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.nc
2023-08-16 16:25:06.835524 +0000        INFO    downloading object s3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.hdf as /tmp/tmpw__agpjf/MOD13Q1.A2004353.h02v11.061.2020213145209.hdf in chunks of 10485760 bytes ...
...
2023-08-16 16:25:24.272118 +0000        INFO    uploading file /tmp/tmpw__agpjf/MOD13Q1.A2004353.h02v11.061.2020213145209.nc as s3://my-bucket/MOD13Q1.A2004353.h02v11.061.2020213145209.nc in chunks of 10485760 bytes ...
2023-08-16 16:25:26.487522 +0000        INFO    conversion took 19.65490329102613 seconds.
```
