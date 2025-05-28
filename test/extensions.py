from geohash_tools import encode

from ies_tool.ies_tool import Device, GeoPoint, IESTool

ADDITONAL_CLASSES = {
    "http://ies.data.gov.uk/ontology/ies4#Widget": ['http://ies.data.gov.uk/ontology/ies4#Device'],
    "http://ies.data.gov.uk/ontology/ies4#Gizmo": ['http://ies.data.gov.uk/ontology/ies4#Device']
}

tool = IESTool()
tool.add_classes(ADDITONAL_CLASSES)

ep = tool.instantiate(classes=["http://ies.data.gov.uk/ontology/ies4#ExchangePayload"])
print(type(ep))
dev1 = tool.instantiate(classes=["http://ies.data.gov.uk/ontology/ies4#Widget"])
print(type(dev1))
dev2 = Device(tool=tool)
lat = 23.4567891234
lon = 12.3456891234
GeoPoint(
    tool=tool,
    lat=lat,
    lon=lon
)
base_uri = "http://geohash.org/" + str(encode(float(lat), float(lon), precision=6))
print(base_uri)
tool.save_rdf("extension.ttl",rdf_format="ttl")
