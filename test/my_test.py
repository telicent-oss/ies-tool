from rdflib import Graph

import ies_tool.ies_tool as ies

tool = ies.IESTool(mode="rdflib")

tool.clear_graph()


# create a geopoint triples

gp = ies.GeoPoint(tool=tool,
                            lat = "50.69391243207585",
                            lon = "-1.2973339742186603",
                            precision = 11)

# create an entity with an identifier that is numeric

person = ies.Person(tool=tool,
                    given_name="John",
                    surname="Smith",
                    date_of_birth="1985-08-21",
                    end="2024-01-01")
person.add_representation("1234567890", literal_type="decimal")

tool.add_literal_property(person.uri, ies.IES_BASE + "hasIdentifier", "123", "float")

# create an entity with an identifier that is a string
location = ies.Location(tool=tool)
location.add_identifier("ABC")

# create a measure with  a value


graph = Graph()
tool.save_rdf(filename = "test/output.ttl",
                       rdf_format="ttl")
