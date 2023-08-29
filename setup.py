import os
from setuptools import find_packages, setup

pkg_name = 'modisconverter'
project_url = 'https://github.com/nasa/modisconverter'


def file_to_list(filepath):
    with open(filepath) as f:
        return f.read().strip().split('\n')


def get_version():
    with open(
        os.path.join(pkg_name, 'common', 'data', 'versions.csv')
    ) as f:
        cols = None
        for ln in f:
            row = ln.split(',')
            if not cols:
                cols = row
                continue
            row = dict(zip(cols, row))
            if row['Current'] == 'True':
                return row['Version']


def get_desc_info():
    with open('README.md') as f:
        return f.read(), 'text/markdown'


desc_content, desc_media = get_desc_info()

setup(
    name=pkg_name,
    version=get_version(),
    description='A library for converting MODIS data files',
    long_description=desc_content,
    long_description_content_type=desc_media,
    url=project_url,
    packages=find_packages(include=[pkg_name, f'{pkg_name}.*']),
    python_requires='>=3.9, <4',
    install_requires=file_to_list('requirements.txt'),
    extras_require={
        'dev': file_to_list('requirements-dev.txt'),
    },
    include_package_data=True,
    test_suite='tests',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
    keywords='MODIS, Converter, HDF4, NetCDF4'
)