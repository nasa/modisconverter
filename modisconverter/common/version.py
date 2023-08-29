import os
import pandas as pd


def _get_versions_from_csv():
    """
    Gets a dataframe object from the versions file
    Returns:
        (pandas.DataFrame): the columnar data read from the file
    """
    return pd.read_csv(
        os.path.join(os.path.dirname(__file__), 'data', 'versions.csv')
    )


def get_current_version():
    """
    Gets the current version of the library

    Returns:
        (dict): info pertaining to the current version
    """
    df = _get_versions_from_csv()
    loc = df.loc[df.Current == True]
    if loc.empty:
        return
    return loc.to_dict(orient='records')[0]


def get_version(ver):
    """
    Gets a version of the library

    Returns:
        (dict): info pertaining to the specified version
    """
    df = _get_versions_from_csv()
    loc = df.loc[df.Version == ver]
    if loc.empty:
        return
    return loc.to_dict(orient='records')[0]


def get_library_identifier():
    return f'modisconverter v{get_current_version()["Version"]}'
