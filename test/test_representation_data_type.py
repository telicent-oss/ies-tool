import unittest

from geohash import encode

import ies_tool.ies_tool as ies


class TestRepresentationDataType(unittest.TestCase):
    tool = None
    save_rdf = False
    file_name = 'test/test_representations.ttl'

    @classmethod
    def setUpClass(cls):
        cls.tool = ies.IESTool(mode="rdflib")
        cls.tool.clear_graph()


    def test_geo_point_datatypes(self):
        latitude = 51.5074
        longitude = -0.0796
        latitude2 = 23.4567
        longitude2 = 12.3456

        ies.GeoPoint(
            tool=self.tool,
            lat=latitude,
            lon=longitude,
            precision = 5
        )

        ies.GeoPoint(
            tool=self.tool,
            lat=latitude2,
            lon=longitude2,
            precision = 5,
            literal_type="string"
        )

        query = """
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {
            ?geopoint1 a ies:GeoPoint ;
                    ies:isIdentifiedBy ?lat1 ;
                    ies:isIdentifiedBy ?lon1 .

            ?lat1 a ies:Latitude ;
                ies:representationValue ?latValue1 .
            ?lon1 a ies:Longitude ;
                ies:representationValue ?lonValue1 .

            ?geopoint2 a ies:GeoPoint ;
                    ies:isIdentifiedBy ?lat2 ;
                    ies:isIdentifiedBy ?lon2 .

            ?lat2 a ies:Latitude ;
                ies:representationValue ?latValue2 .
            ?lon2 a ies:Longitude ;
                ies:representationValue ?lonValue2 .

            FILTER(DATATYPE(?latValue1) = xsd:decimal && DATATYPE(?lonValue1) = xsd:decimal &&
                   DATATYPE(?latValue2) = xsd:string && DATATYPE(?lonValue2) = xsd:string)
        }
        """


        result = self.tool.graph.query(query)
        self.assertTrue(result)

    # tests that representation of name defaults to string
    def test_name_type(self):
        ies.Name(tool = self.tool,
                 name_text = "Anne")
        query = """
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {
            ?name a ies:Name ;
                ies:representationValue ?annes_name .

            FILTER(DATATYPE(?annes_name) = xsd:string )
        }
        """

        result = self.tool.graph.query(query)
        self.assertTrue(result)


    #test that identifier defaults to string but can be changed to other data type
    def test_identifier_type(self):
        # Test default string identifier
        ies.Identifier(
            tool=self.tool,
            id_text="ID123"
        )

        # Test decimal identifier
        ies.Identifier(
            tool=self.tool,
            id_text=456,
            literal_type="decimal"
        )

        # Test float identifier
        ies.Identifier(
            tool=self.tool,
            id_text=456.789,
            literal_type="float"
        )

        query = """
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {
            ?id1 a ies:Identifier ;
                ies:representationValue ?value1 .
            ?id2 a ies:Identifier ;
                ies:representationValue ?value2 .
            ?id3 a ies:Identifier ;
                ies:representationValue ?value3 .
            FILTER(DATATYPE(?value1) = xsd:string &&
                   DATATYPE(?value2) = xsd:decimal &&
                   DATATYPE(?value3) = xsd:float)
        }
        """

        result = self.tool.graph.query(query)
        self.assertTrue(result, "Identifiers do not have correct datatypes")

    #test that measureValue defaults to string but can be changed to other data type
    def test_measure_data_type(self):
        # test measureValue with string value (default)
        ies.MeasureValue(
            tool=self.tool,
                value="100",
        )

        # test measureValue with decimal value
        ies.MeasureValue(
            tool=self.tool,
            value='100',
            literal_type="decimal",
        )

        # test measureValue with float value
        ies.MeasureValue(
            tool=self.tool,
            value='100.0',
            literal_type="float",
        )

        query = """
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {
            ?measurevalue1 a ies:MeasureValue ;
                     ies:representationValue ?value1 .

            ?measurevalue2 a ies:MeasureValue ;
                     ies:representationValue ?value2 .

            ?measurevalue3 a ies:MeasureValue ;
                     ies:representationValue ?value3 .

            FILTER(DATATYPE(?value1) = xsd:string &&
                   DATATYPE(?value2) = xsd:decimal &&
                   DATATYPE(?value3) = xsd:float)
        }
        """


        result = self.tool.graph.query(query)
        self.assertTrue(result, "Measure values should have correct datatypes (string, decimal and float)")

    # test that lat/lon URI defaults to precision of 6 decimal places
    def test_geo_point_default_precision(self):
        lat = 23.4567891234
        lon = 12.3456891234
        ies.GeoPoint(
            tool=self.tool,
            lat=lat,
            lon=lon
        )

        base_uri = "http://geohash.org/" + str(encode(float(lat), float(lon), precision=6))
        lat_uri = f"{base_uri}_LAT"
        lon_uri = f"{base_uri}_LON"

        query = f"""
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {{
            <{base_uri}> a ies:GeoPoint ;
                    ies:isIdentifiedBy <{lat_uri}> ;
                    ies:isIdentifiedBy <{lon_uri}> .

            <{lat_uri}> a ies:Latitude .
            <{lon_uri}> a ies:Longitude .
        }}
        """

        result = self.tool.graph.query(query)
        self.assertTrue(result, "GeoPoint should create URIs with default precision of 6")

    @classmethod
    def tearDownClass(cls):
        # Save all  data
        if cls.save_rdf:
            cls.tool.graph.serialize(destination=cls.file_name, format='turtle')
            print(f"Complete RDF graph saved to {cls.file_name}")


if __name__ == '__main__':
    unittest.main()
