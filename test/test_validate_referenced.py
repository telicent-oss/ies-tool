from ies_tool.ies_tool import Event, IESTool

IES_BASE = "http://ies.data.gov.uk/ontology/ies4#"
file_name = "sample_participant.ttl"
data_ns = "http://telicent.io/data#"
participant_uri = data_ns + "event_participant_A"

tool = IESTool(mode="rdflib")


tool.add_prefix("data:", data_ns)

# create event
my_event =Event(tool=tool,uri =data_ns +"my_event" )
print(my_event._classes)

# add participant to event
    # expected inferred class: Entity
    # actual inferred class: RdfsResource
my_event.add_participant(participating_entity = participant_uri)

# save rdf
tool.graph.serialize(destination=file_name, format='turtle')

print(f"RDF graph saved to {file_name}")
