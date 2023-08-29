from abc import ABC, abstractmethod

MODIS_PROJECTION_IDENTIFIER = 'modis_sinusoidal'


def get_projection(identifier):
    if identifier == MODIS_PROJECTION_IDENTIFIER:
        return ModisSinusoidal()
    else:
        raise ValueError(f'projection {identifier} is not supported.')


class Projection(ABC):
    @property
    def indentifier(self):
        return self._identifier

    @property
    def proj4(self):
        return self._proj4

    @property
    def ogc_wkt(self):
        return self._ogc_wkt

    @abstractmethod
    def get_netcdf_attrs():
        pass


class ModisSinusoidal(Projection):
    def __init__(self):
        self._identifier = MODIS_PROJECTION_IDENTIFIER
        self._proj4 = (
            '+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs=True')
        self._ogc_wkt = (
            'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",'
            'DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid"'
            ',6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,'
            'AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],'
            'PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],'
            'PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],'
            'AXIS["Northing",NORTH]]')

    def get_crs_properties(self):
        return {
            'units': 'm',
            'y_dimension_standard_name': 'projection_y_coordinate',
            'x_dimension_standard_name': 'projection_x_coordinate'
        }

    def get_netcdf_attrs(self):
        return {
            'grid_mapping_name': 'sinusoidal',
            '_CoordinateAxisTypes': 'GeoX GeoY',
            'semi_major_axis': 6371007.181,
            'longitude_of_central_meridian': 0.0,
            'longitude_of_projection_origin': 0.0,
            'straight_vertical_longitude_from_pole': 0.0,
            'false_easting': 0.0,
            'false_northing': 0.0,
            'proj4text': self.proj4,
            'crs_wkt': self.ogc_wkt,
            'spatial_ref': self.ogc_wkt
        }
