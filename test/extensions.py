from ies_tool.ies_tool import IES_TOOL, IESTool, Device

ADDITONAL_CLASSES = {
    "http://ies.data.gov.uk/ontology/ies4#Widget": ['http://ies.data.gov.uk/ontology/ies4#Device'],
    "http://ies.data.gov.uk/ontology/ies4#Gizmo": ['http://ies.data.gov.uk/ontology/ies4#Device']
}

tool = IESTool()

ep = tool.instantiate(classes=["http://ies.data.gov.uk/ontology/ies4#ExchangePayload"])
print(type(ep))
dev1 = tool.instantiate(classes=["http://ies.data.gov.uk/ontology/ies4#Device"])
print(type(dev1))
dev2 = Device(tool=tool)
tool.save_rdf("extension.ttl",rdf_format="ttl")
