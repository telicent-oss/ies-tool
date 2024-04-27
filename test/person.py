from ies_tool.ies_tool import Account, Country, IESTool, Person

tool = IESTool(validate=True)

my_person = Person(
    tool=tool,
    given_name='Fred',
    surname='Smith',
    date_of_birth="1985-08-21",
    end="2024-01-01"
)

my_person.add_given_name("Bernard")
my_person.add_given_name("Lester")

my_country = Country(tool=tool,country_alpha_3_code="GBR",country_name="Blighty")

my_account = Account(tool=tool)
my_account.add_account_holder(my_person)
my_account.add_registered_telephone_number("+44 7768 899399")
my_account.add_registered_email_address("fred.smith@fakedomain.int")

tool.save_rdf('./person.ttl', format="ttl")
