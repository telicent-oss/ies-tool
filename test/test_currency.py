import unittest

import ies_tool.ies_tool as ies


class TestCurrencyNameAndIdentifier(unittest.TestCase):
    def setUp(self):
        self.tool = ies.IESTool(mode="rdflib")
        self.clear_graph()
        self.save_rdf = False
        self.file_name = "test/test_currency.ttl"

    def clear_graph(self):
        self.tool.clear_graph()

    def test_currency_uris(self):
        # Create amount of money in Pakistani rupees (PKR)
        ies.AmountOfMoney(tool=self.tool, amount=100.0, iso_4217_currency_code_alpha3="PKR")

        # deterministic URIs
        currency_uri = "http://iso.org/iso4217#PKR"
        identifier_uri = f"{currency_uri}_ISO4217_alpha3"
        name_uri = f"{currency_uri}_NAME"

        id_query = f"""
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {{
            <{currency_uri}> ies:isIdentifiedBy <{identifier_uri}> .
            <{identifier_uri}> ies:representationValue "PKR"^^xsd:string .
        }}
        """

        name_query = f"""
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ASK {{
            <{currency_uri}> ies:hasName <{name_uri}> .
            <{name_uri}> ies:representationValue "Pakistani rupee"^^xsd:string .
        }}
        """

        id_exists = self.tool.graph.query(id_query).askAnswer
        name_exists = self.tool.graph.query(name_query).askAnswer

        self.assertTrue(id_exists, "Currency identifier URI not found or incorrect")
        self.assertTrue(name_exists, "Currency name URI not found or incorrect")

        if self.save_rdf:
            self.tool.graph.serialize(destination=self.file_name, format='turtle')
            print(f"RDF graph saved to {self.file_name}")
