from ies_tool.ies_tool import IES_TOOL, IESTool

ADDITONAL_CLASSES = {
    "http://ies.data.gov.uk/ontology/ies4#Widget": ['http://ies.data.gov.uk/ontology/ies4#Device'],
    "http://ies.data.gov.uk/ontology/ies4#Gizmo": ['http://ies.data.gov.uk/ontology/ies4#Device']
}


IES_TOOL.save_rdf("extension.ttl",format="ttl")

tool = IESTool(mode="rdflib")
ep = tool.instantiate(classes=["http://ies.data.gov.uk/ontology/ies4#ExchangePayload"])
