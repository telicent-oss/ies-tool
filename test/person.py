from ies_tool.ies_tool import IESTool, Person

tool = IESTool(validate=True)

my_person = Person(
    tool=tool,
    given_name='Fred',
    family_name='Smith',
    date_of_birth="1985-08-21"
)

tool.save_rdf('./person.ttl', format="ttl")