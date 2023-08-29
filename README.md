# modisconverter

`modisconverter` is a Python package that converts MODIS data from HDF4 to NetCDF4 file format.

## Prequisites

- Python >= 3.9
- GDAL >= 3.1.2, with supported file formats `HDF4` and `netCDF`

## Installation

This package is available on [PyPI](https://pypi.org/project/modisconverter/) and can be installed with [pip](https://pip.pypa.io/en/stable/user_guide/).

Package install depends on having a Python `GDAL` package that matches the version of the underlying GDAL installation. It also requires the `rasterio` package to be built from source.

```bash
$ pip install GDAL==<installed-version-number> --no-binary rasterio modisconverter
```

e.g.

```bash
$ pip install GDAL==3.6.3 --no-binary rasterio modisconverter
```

You can find your installed GDAL version by using the `gdal-config` binary:

```bash
$ gdal-config --version
```

## Environment Considerations

It's recommended to install the package in a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/). Otherwise, if your machine can run Docker containers, installing the package in one provides natural isolation.

For potential Docker images, you could consider using one of the [official GDAL images](https://hub.docker.com/r/osgeo/gdal/tags) from DockerHub, which contain a GDAL and Python installation.  For instance, the Ubuntu-based image `ghcr.io/osgeo/gdal:ubuntu-full-3.6.3`.  Note that the `pip` package manager may not be installed in such images.

## Usage

```python
from modisconverter import convert_file

src = 'example-modis.hdf'
dst = 'example-modis.nc'
convert_file(src, dst)
```

## Documentation

Listed below are various documents pertaining to this project.

- [Changelog](CHANGELOG.md) - Information on releases.
- [Usage](docs/USAGE.md) - Detailed usage of the library.
