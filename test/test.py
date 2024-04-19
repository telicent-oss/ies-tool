import time
from unittest import TestCase
from unittest.mock import mock_open, patch

from ies_tool.ies_tool import Element, Entity, IESTool, Person


def sparql_test():
    tool = IESTool(mode="sparql_server", validate=False, server_dataset="ontology")
    tool.run_sparql_update("INSERT DATA {<http://a> a <http://x>}")
    tool.run_sparql_update("INSERT DATA {<http://a> <http://b> <http://c>}")
    tool.add_to_graph("http://a","http://y","http://z",False)
    tool.add_to_graph("http://a","http://t","test literal",True)
    out = tool.run_sparql_query("SELECT * WHERE { <http://a> ?p ?o } LIMIT 4")
    print(out)
    tool.delete_triple("http://a",tool.rdf_type,"http://x")
    tool.delete_triple("http://a","http://b","http://c")
    tool.delete_triple("http://a","http://y","http://z")
    tool.delete_triple("http://a","http://t","test literal",True)
    time.sleep(1)
    out = tool.run_sparql_query("SELECT * WHERE { <http://a> ?p ?o } LIMIT 4")
    print(out)


def run_test(tool):
    for c in tool.ontology.classes:
        inst = tool.instantiate([c])
        if isinstance(inst, Element):
            # obviously, this will be wrong for most classes, but we're just testing performance
            inst.add_state(start="2004-01-01", end="2006-01-01")
        for _ in range(50):
            dev = Entity(tool=tool, classes=["http://ies.data.gov.uk/ontology/ies4#Device"])
            dev.add_state(state_type=tool.ontology.ies_class("DeviceState"), start="2014-03-11", end="2022-08-30")
        tool.get_rdf()
        tool.clear_graph()


def test_anne_person():
    tool = IESTool(validate=True)
    anne = Person(tool=tool, given_name="Anne", family_name="Smith")
    anne.add_measure(measure_class=tool.ontology.ies_class("Mass"), value=104)

    anne.add_identifier("blah")
    anne.add_name("blah name")
    anne.add_label("Anne Label")
    anne.add_representation("blah rep")

    tool.instantiate(
        ["http://ies.data.gov.uk/ontology/ies4#Device", "http://ies.data.gov.uk/ontology/ies4#Person"]
    )

    gp = tool.create_geopoint(lat=52.41419458448101, lon=16.899256413657202, precision=9)
    e = tool.create_event()
    e.add_participant(anne)

    acme = tool.create_organisation(name="ACME inc")
    acme_director = acme.add_post(name="Witchfinder General", start="1612-01-01")
    acme.add_part("http://test#part1") #A test to see if dumb URIs can be passed

    anne.add_birth("1984-01-01", gp)
    anne.add_death("2017-08-11", gp)
    anne.add_state()
    anne.works_for(acme, "2011-03-11", "2017-06-20")

    anne.in_post(acme_director, start="2015-12-05", end="2017-06-20")

    comm = tool.create_communication()
    comm.add_participant(anne)
    comm.add_participant("http://test#particpant1")
    tool.save_rdf('./test-anne.ttl', format="ttl")


class MainTestCase(TestCase):

    def setUp(self):
        self.tool = IESTool(validate=True)

    @staticmethod
    def test_anne_person():
        with patch("builtins.open", mock_open()) as mock_file:
            test_anne_person()
            mock_file.assert_called_with('./test-anne.ttl', 'w')

    def test_no_dob_on_person_when_none(self):
        Person(tool=self.tool, given_name="Anne", family_name="Smith")
        self.assertTrue('BIRTH' not in str(self.tool.get_rdf()))

    def test_dob_on_person_when_given(self):
        Person(tool=self.tool, given_name="Anne", family_name="Smith", start='1970-01-01')
        self.assertTrue('BIRTH' in str(self.tool.get_rdf()))


if __name__ == '__main__':
    print(f"{'==='*45}")
    # sparql_test()
    print("SPARQL test complete.")

    print(f"{'==='*45}")
    test_anne_person()
    print("Test anne person complete.")

    print(f"{'==='*45}")
