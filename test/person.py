from ies_tool.ies_tool import Account, AmountOfMoney, Country, Device, IESTool, Person

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

my_device = Device(tool=tool)
my_device.add_callsign("RUBBER DUCK")
my_device.add_mac_address("01:23:45:67:ab:CD")
my_device.add_imsi("IMSI:310170845466094")
my_device.add_ip_address("2001:0000:130F:0000:0000:09C0:876A:130B")

my_person.owns(my_device)

my_amount = AmountOfMoney(tool=tool,iso_4217_currency_code_alpha3="CHF",amount=32.56)

my_person.owns(my_amount)

tool.save_rdf('./person.ttl', format="ttl")
