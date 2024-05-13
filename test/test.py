import time
from unittest import TestCase
from unittest.mock import mock_open, patch

from ies_tool.ies_tool import IES_TOOL, Communication, Element, Entity, Event, GeoPoint, IESTool, Organisation, Person


def sparql_test():
    #tool = IESTool(mode="sparql_server", validate=False, server_dataset="ontology")
    IES_TOOL.run_sparql_update("INSERT DATA {<http://a> a <http://x>}")
    IES_TOOL.run_sparql_update("INSERT DATA {<http://a> <http://b> <http://c>}")
    IES_TOOL.add_to_graph("http://a","http://y","http://z",False)
    IES_TOOL.add_to_graph("http://a","http://t","test literal",True)
    out = IES_TOOL.run_sparql_query("SELECT * WHERE { <http://a> ?p ?o } LIMIT 4")
    print(out)
    IES_TOOL.delete_triple("http://a",IES_TOOL.rdf_type,"http://x")
    IES_TOOL.delete_triple("http://a","http://b","http://c")
    IES_TOOL.delete_triple("http://a","http://y","http://z")
    IES_TOOL.delete_triple("http://a","http://t","test literal",True)
    time.sleep(1)
    out = IES_TOOL.run_sparql_query("SELECT * WHERE { <http://a> ?p ?o } LIMIT 4")
    print(out)


def run_test(tool=IES_TOOL):
    for c in tool.ontology.classes:
        inst = tool.instantiate([c])
        if isinstance(inst, Element):
            # obviously, this will be wrong for most classes, but we're just testing performance
            inst.create_state(start="2004-01-01", end="2006-01-01")
        for _ in range(50):
            dev = Entity(tool=tool, classes=["http://ies.data.gov.uk/ontology/ies4#Device"])
            dev.create_state(state_type=tool.ontology.ies_class("DeviceState"), start="2014-03-11", end="2022-08-30")
        tool.get_rdf()
        tool.clear_graph()


def test_anne_person():
    IES_TOOL.clear_graph()
    anne = Person(given_name="Anne", surname="Smith", date_of_birth="1492-01-13")
    anne.add_measure(measure_class=IES_TOOL.ontology.ies_class("Mass"), value=104)

    anne.add_identifier("blah")
    anne.add_name("blah name")
    anne.add_label("Anne Label")
    anne.add_representation("blah rep")

    IES_TOOL.instantiate(
        ["http://ies.data.gov.uk/ontology/ies4#Device", "http://ies.data.gov.uk/ontology/ies4#Person"]
    )

    gp = GeoPoint(lat=52.41419458448101, lon=16.899256413657202, precision=9)
    e = Event(end="1999-09-09")
    e.add_participant(anne)

    acme = Organisation(name="ACME inc")
    acme_director = acme.create_post(name="Witchfinder General", start="1612-01-01")
    acme.add_part("http://test#part1") #A test to see if dumb URIs can be passed

    anne.add_birth("1984-01-01", gp)
    anne.add_death("2017-08-11", gp)
    anne.create_state()
    anne.works_for(acme, "2011-03-11", "2017-06-20")

    anne.in_post(acme_director, start="2015-12-05", end="2017-06-20")

    comm = Communication()
    comm.add_participant(anne)
    comm.add_participant("http://test#particpant1")
    IES_TOOL.save_rdf('./test-anne.ttl', rdf_format="ttl")


class MainTestCase(TestCase):

    def setUp(self):
        self.tool = IESTool(validate=True)

    @staticmethod
    def test_anne_person():
        with patch("builtins.open", mock_open()) as mock_file:
            test_anne_person()
            mock_file.assert_called_with('./test-anne.ttl', 'w')

    def test_no_dob_on_person_when_none(self):
        Person(tool=self.tool, given_name="Anne", surname="Smith")
        self.assertTrue('BIRTH' not in str(self.tool.get_rdf()))

    def test_dob_on_person_when_given(self):
        Person(tool=self.tool, given_name="Anne", surname="Smith", start='1970-01-01')
        self.assertTrue('BIRTH' in str(self.tool.get_rdf()))


if __name__ == '__main__':
    print(f"{'==='*45}")
    # sparql_test()
    print("SPARQL test complete.")

    print(f"{'==='*45}")
    test_anne_person()
    print("Test anne person complete.")

    print(f"{'==='*45}")
