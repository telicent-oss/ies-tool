import unittest

import ies_tool.ies_tool as ies


class TestCountryNameAndIdentifier(unittest.TestCase):
    def setUp(self):
        self.tool = ies.IESTool(mode="rdflib")
        self.clear_graph()
        self.save_rdf = False
        self.file_name = "test/test_country.ttl"

    def clear_graph(self):
        self.tool.clear_graph()

    def test_country_uris(self):
        # Create a country
        ies.Country(tool=self.tool, country_alpha_3_code="PAK", country_name="Pakistan")

        # deterministic URIs
        country_uri = "http://iso.org/iso3166/country#PAK"
        identifier_uri = f"{country_uri}_ISO3166_1Alpha_3"
        name_uri = f"{country_uri}_NAME_001"

        id_query = f"""
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {{
            <{country_uri}> ies:isIdentifiedBy <{identifier_uri}> .
            <{identifier_uri}> ies:representationValue "PAK"^^xsd:string .
        }}
        """

        name_query = f"""
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {{
            <{country_uri}> ies:hasName <{name_uri}> .
            <{name_uri}> ies:representationValue "Pakistan"^^xsd:string .
        }}
        """

        id_exists = self.tool.graph.query(id_query).askAnswer
        name_exists = self.tool.graph.query(name_query).askAnswer


        if self.save_rdf:
            self.tool.graph.serialize(destination=self.file_name, format='turtle')
            print(f"RDF graph saved to {self.file_name}")

        self.assertTrue(id_exists, "Country identifier URI not found or incorrect")
        self.assertTrue(name_exists, "Country name URI not found or incorrect")
