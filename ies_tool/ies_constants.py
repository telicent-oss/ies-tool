RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDFS_RESOURCE = "http://www.w3.org/2000/01/rdf-schema#Resource"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_CLASS = "http://www.w3.org/2000/01/rdf-schema#Class"

IES_BASE = "http://ies.data.gov.uk/ontology/ies4#"
DEFAULT_DATA_NAMESPACE = "http://example.com/rdf/testdata#"

TELICENT_PRIMARY_NAME = "http://telicent.io/ontology/primaryName"

THING = f"{IES_BASE}Thing"
ELEMENT = f"{IES_BASE}Element"
CLASS_OF_ELEMENT = f"{IES_BASE}ClassOfElement"
CLASS_OF_CLASS_OF_ELEMENT = f"{IES_BASE}ClassOfClassOfElement"
PARTICULAR_PERIOD = f"{IES_BASE}ParticularPeriod"
ACCOUNT = f"{IES_BASE}Account"
ACCOUNT_HOLDER = f"{IES_BASE}AccountHolder"
ACCOUNT_STATE = f"{IES_BASE}AccountState"
AMOUNT_OF_MONEY = f"{IES_BASE}AmountOfMoney"
ASSET = f"{IES_BASE}Asset"
ASSET_STATE = f"{IES_BASE}AssetState"
COMMUNICATIONS_ACCOUNT = f"{IES_BASE}CommunicationsAccount"
COMMUNICATIONS_ACCOUNT_STATE = f"{IES_BASE}CommunicationsAccountState"
HOLDS_ACCOUNT = f"{IES_BASE}holdsAccount"
PROVIDES_ACCOUNT = f"{IES_BASE}providesAccount"
STATE = f"{IES_BASE}State"
BOUNDING_STATE = f"{IES_BASE}BoundingState"
BIRTH_STATE = f"{IES_BASE}BirthState"
DEATH_STATE = f"{IES_BASE}DeathState"
UNIT_OF_MEASURE = f"{IES_BASE}UnitOfMeasure"
MEASURE_VALUE = f"{IES_BASE}MeasureValue"
MEASURE = f"{IES_BASE}Measure"
REPRESENTATION = f"{IES_BASE}Representation"
IDENTIFIER = f"{IES_BASE}Identifier"
NAME = f"{IES_BASE}Name"
NAMING_SCHEME = f"{IES_BASE}NamingScheme"
ENTITY = f"{IES_BASE}Entity"
DEVICE_STATE = f"{IES_BASE}DeviceState"
DEVICE = f"{IES_BASE}Device"
LOCATION = f"{IES_BASE}Location"
LOCATION_STATE = f"{IES_BASE}#LocationState"
COUNTRY = f"{IES_BASE}Country"
GEOPOINT = f"{IES_BASE}GeoPoint"
RESPONSIBLE_ACTOR = f"{IES_BASE}ResponsibleActor"
POST = f"{IES_BASE}Post"
PERSON = f"{IES_BASE}Person"
ORGANISATION = f"{IES_BASE}Organisation"
ORGANISATION_NAME = f"{IES_BASE}OrganisationName"
EVENT = f"{IES_BASE}Event"
EVENT_PARTICIPANT = f"{IES_BASE}EventParticipant"
COMMUNICATION = f"{IES_BASE}Communication"
PARTY_IN_COMMUNICATION = f"{IES_BASE}PartyInCommunication"
WORK_OF_DOCUMENTATION = f"{IES_BASE}WorkOfDocumentation"

DEFAULT_PREFIXES = {
    "xsd:": "http://www.w3.org/2001/XMLSchema#",
    "dc:": "http://purl.org/dc/elements/1.1/",
    "rdf:": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs:": "http://www.w3.org/2000/01/rdf-schema#",
    "owl:": "http://www.w3.org/2002/07/owl#",
    "iso8601:": "http://iso.org/iso8601#",
    "iso3166c:": "http://iso.org/iso3166/country#",
    "iso4217:": "http://iso.org/iso4217#",
    "tont:": "http://telicent.io/ontology/",
    "e164:": "https://www.itu.int/e164#",
    "IMSI:": "https://www.itu.int/e212#",
    "rfc5322:": "https://ietf.org/rfc5322#",
    "ieee802:": "https://www.ieee802.org#",
    "ies:": IES_BASE,
    ":": "http://example.com/rdf/testdata#",
}
