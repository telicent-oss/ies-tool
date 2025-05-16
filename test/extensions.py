from ies_tool.ies_tool import IES_TOOL, Device, RdfsResource

ADDITONAL_CLASSES = {
    "http://ies.data.gov.uk/ontology/ies4#Widget": ['http://ies.data.gov.uk/ontology/ies4#Device'],
    "http://ies.data.gov.uk/ontology/ies4#Gizmo": ['http://ies.data.gov.uk/ontology/ies4#Device']
}


IES_TOOL.save_rdf("extension.ttl",format="ttl")
