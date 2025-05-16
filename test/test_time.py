import unittest

import ies_tool.ies_tool as ies


class TestDateTimeValidation(unittest.TestCase):
    def setUp(self):
        self.tool = ies.IESTool(mode="rdflib")
        self.clear_graph()
        self.save_rdf = False
        self.file_name = "test/test_dates.ttl"

    def clear_graph(self):
        self.tool.clear_graph()


    def test_invalid_dates(self):
        invalid_dates = [
            "2024/01/01",        # Wrong separator
            "2024-13-01",        # Invalid month
            "2024-01-32",        # Invalid day
            "2024-01-01+3:00",   # timezone offset
            "202",               # Incomplete year
            "2024-1",            # Incomplete month
            "not-a-date",        # Nonsense string
            "2024-01-01T25:00",  # Invalid hour
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

    def test_particular_period_uri_and_literal(self):
        test_cases = [
            {
                "time_string": "2023-05-15",
                "iso8601_time_string_punctuated": "2023-05-15",
                "iso8601_time_string_non_punctuated": "20230515"
            },
            {
                "time_string": "2024-03-03T12:00:00",
                "iso8601_time_string_punctuated": "2024-03-03T12:00:00",
                "iso8601_time_string_non_punctuated": "20240303T120000"
            },
            {
                "time_string": "2024-01-01T12:00:00Z",
                "iso8601_time_string_punctuated": "2024-01-01T12:00:00",
                "iso8601_time_string_non_punctuated": "20240101T120000"
            },
            {
                "time_string": "2007-01-18 15:30:00",
                "iso8601_time_string_punctuated": "2007-01-18T15:30:00",
                "iso8601_time_string_non_punctuated": "20070118T153000"
            },

            {
                "time_string": "2021",
                "iso8601_time_string_punctuated": "2021",
                "iso8601_time_string_non_punctuated": "2021"
            },
            {
                "time_string": "2020-06",
                "iso8601_time_string_punctuated": "2020-06",
                "iso8601_time_string_non_punctuated": "202006"
            }
        ]



        for case in test_cases:
            with self.subTest(case=case):
                ies.ParticularPeriod(
                    tool=self.tool,
                    time_string=case["time_string"]
                )

                # Verify the URI
                expected_uri = f"http://iso.org/iso8601#{case['iso8601_time_string_non_punctuated']}"

                # Verify the triple exists in the graph using ASK query
                query = f"""
                PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                ASK {{
                    <{expected_uri}> a ies:ParticularPeriod ;
                        ies:iso8601PeriodRepresentation "{case['iso8601_time_string_punctuated']}"^^xsd:string .
                }}
                """

                result = self.tool.graph.query(query).askAnswer
                self.assertTrue(result, f"Triple for time string {case['time_string']} not found in graph")


        if self.save_rdf:
            self.tool.graph.serialize(destination=self.file_name, format='turtle')
            print(f"RDF graph saved to {self.file_name}")
if __name__ == '__main__':
    unittest.main()




