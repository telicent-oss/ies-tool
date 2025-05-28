import unittest

import ies_tool.ies_tool as ies


class TestInferredClasses(unittest.TestCase):
    def setUp(self):
        self.tool = ies.IESTool(mode="rdflib")
        self.clear_graph()
        self.save_rdf = True
        self.file_name = "test/test_inferred_classes.ttl"
        self.IES_BASE = "http://ies.data.gov.uk/ontology/ies4#"
        self.file_name = "sample_participant.ttl"
        self.data_ns = "http://telicent.io/data#"
        self.participating_entity_uri = self.data_ns + "participating_person_A"
        self.participant_uri = self.data_ns + "event_participant_A"

    def clear_graph(self):
        self.tool.clear_graph()

    def test_inferred_classes(self):
        # Create event with a participating entity
        my_event =ies.Event(tool=self.tool,uri =self.data_ns +"my_event" )
        my_event.add_participant(participating_entity = self.participating_entity_uri,
                                 uri = self.participant_uri)

        participant_query = """
        PREFIX ies: <http://ies.data.gov.uk/ontology/ies4#>
        ASK {
            ?participant a ies:EventParticipant ;
                        ies:isParticipationOf ?participating_entity ;
                        ies:isParticipantIn ?event .

            ?event a ies:Event .
            ?participating_entity a ies:Entity .
        }
        """

        result = self.tool.graph.query(participant_query)
        self.assertTrue(result, "Participation pattern not found or incorrect")


        if self.save_rdf:
            self.tool.graph.serialize(destination=self.file_name, format='turtle')
            print(f"RDF graph saved to {self.file_name}")


