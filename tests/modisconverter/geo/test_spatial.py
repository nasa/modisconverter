from unittest import TestCase, main
from modisconverter.geo import spatial


class TestSpatial(TestCase):
    def test_get_projection_modis(self):
        self.assertIsInstance(
            spatial.get_projection(spatial.MODIS_PROJECTION_IDENTIFIER),
            spatial.ModisSinusoidal
        )

    def test_get_projection_unsupported(self):
        with self.assertRaises(ValueError):
            spatial.get_projection('unknown')


class TestModisSinusoidal(TestCase):
    def test_init(self, return_instance=False):
        actual_inst = spatial.ModisSinusoidal()
        if return_instance:
            return actual_inst

        expected_proj4 = '+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs=True'
        expected_wkt = (
            'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",'
            'DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid"'
            ',6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,'
            'AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],'
            'PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],'
            'PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],'
            'AXIS["Northing",NORTH]]'
        )
        self.assertEqual(actual_inst._identifier, spatial.MODIS_PROJECTION_IDENTIFIER)
        self.assertEqual(actual_inst._proj4, expected_proj4)
        self.assertEqual(actual_inst._ogc_wkt, expected_wkt)

    def test_get_crs_properties(self):
        expected_props = {
            'units': 'm',
            'y_dimension_standard_name': 'projection_y_coordinate',
            'x_dimension_standard_name': 'projection_x_coordinate'
        }
        actual_inst = self.test_init(return_instance=True)

        self.assertEqual(actual_inst.get_crs_properties(), expected_props)

    def test_get_netcdf_attrs(self):
        expected_attrs = {
            'units': 'm',
            'y_dimension_standard_name': 'projection_y_coordinate',
            'x_dimension_standard_name': 'projection_x_coordinate'
        }
        actual_inst = self.test_init(return_instance=True)
        expected_attrs = {
            'grid_mapping_name': 'sinusoidal',
            '_CoordinateAxisTypes': 'GeoX GeoY',
            'semi_major_axis': 6371007.181,
            'longitude_of_central_meridian': 0.0,
            'longitude_of_projection_origin': 0.0,
            'straight_vertical_longitude_from_pole': 0.0,
            'false_easting': 0.0,
            'false_northing': 0.0,
            'proj4text': actual_inst.proj4,
            'crs_wkt': actual_inst.ogc_wkt,
            'spatial_ref': actual_inst.ogc_wkt
        }

        self.assertEqual(actual_inst.get_netcdf_attrs(), expected_attrs)


if __name__ == '__main__':
    main()
