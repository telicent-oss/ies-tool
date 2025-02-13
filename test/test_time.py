import unittest

import ies_tool.ies_tool as ies


class TestDateTimeValidation(unittest.TestCase):
    def setUp(self):
        self.tool = ies.IESTool(mode="rdflib")
        self.clear_graph()
        self.save_rdf = True
        self.file_name = "test/test_dates.ttl"

    def clear_graph(self):
        self.tool.clear_graph()

    def test_valid_dates(self):
        valid_dates = [
            "2024-03-15",           # Simple date
            "2007-03-01T13:00:00",  # Datetime with time
            "2023",                 # Year only
            "2025-07"               # Year and month
        ]

        for date in valid_dates:
            with self.subTest(date=date):
                try:
                    ies.Person(
                        tool=self.tool,
                        given_name="John",
                        surname="Doe",
                        date_of_birth=date
                    )

                    query = f"""
                    PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
                    ASK {{
                        ?ParticularPeriod a ies:ParticularPeriod ;
                               ies:iso8601PeriodRepresentation ?date .
                        FILTER(?date = "{date}")
                    }}
                    """

                    result = self.tool.graph.query(query)
                    self.assertTrue(result, f"Triple for date {date} not found in graph")

                except Exception as e:
                    self.fail(f"Failed to create person with valid date {date}: {str(e)}")

        if self.save_rdf:
            self.tool.graph.serialize(destination=self.file_name, format='turtle')
            print(f"RDF graph saved to {self.file_name}")

    def test_invalid_dates(self):
        invalid_dates = [
            "2024/01/01",        # Wrong separator
            "2024-13-01",        # Invalid month
            "2024-01-32",        # Invalid day
            "202",               # Incomplete year
            "2024-1",            # Incomplete month
            "not-a-date",        # Nonsense string
            "2024-01-01T25:00",  # Invalid hour
            "2024-01-01+25:00"   # Invalid timezone offset
        ]

        for date in invalid_dates:
            with self.subTest(date=date):
                with self.assertRaises(RuntimeError, msg=f"Invalid date {date} should raise RuntimeError"):
                    ies.Person(
                        tool=self.tool,
                        given_name="John",
                        surname="Doe",
                        date_of_birth=date
                    )

if __name__ == '__main__':
    unittest.main()




