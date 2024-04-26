from ies_tool.ies_tool import Country, IESTool, Person

tool = IESTool(validate=True)

my_person = Person(
    tool=tool,
    given_name='Fred',
    surname='Smith',
    date_of_birth="1985-08-21",
    end="2024-01-01"
)

my_country = Country(tool=tool,country_alpha_3_code="GBR",country_name="Blighty")

tool.save_rdf('./person.ttl', format="ttl")
