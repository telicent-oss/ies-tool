from ies_tool.ies_tool import IESTool
from ies_tool.ies_classes import RdfsResource, Country, Account, Device, AmountOfMoney
if __name__ == '__main__':
    IES_TOOL = IESTool.get_instance()
    my_r = RdfsResource(tool=IES_TOOL)
    # my_person = IES_TOOL.create_person(given_name='Fred',
    #     surname='Smith',
    #     date_of_birth="1985-08-21",
    #     date_of_death="2024-01-01")
    my_person = IES_TOOL.create_person(
        given_name='Fred',
        surname='Smith',
        date_of_birth="1985-08-21",
        date_of_death="2024-01-01"
    )

    my_person.add_given_name("Bernard")
    my_person.add_given_name("Lester")
    print(str(my_person.__dict__))
    my_country = Country(tool=IES_TOOL, country_alpha_3_code="GBR",country_name="Blighty")
    print(str(my_country.__dict__))
    # Pay attention to how IESTool object is shared - this is purposely done
    # we can do weird stuff now

    #my_account = Account(tool=IES_TOOL)
    my_account = IES_TOOL.entity_factory.create_entity('aCCoUnT')
    print(str(my_account.__dict__))
    my_account.add_account_holder(my_person)
    my_account.add_registered_telephone_number("+44 7768 899399")
    my_account.add_registered_email_address("fred.smith@fakedomain.int")

    my_device = Device(IES_TOOL)
    my_device.add_callsign("RUBBER DUCK")
    my_device.add_mac_address("01:23:45:67:ab:CD")
    my_device.add_imsi("IMSI:310170845466094")
    my_device.add_ip_address("2001:0000:130F:0000:0000:09C0:876A:130B")

    my_person.owns(my_device)

    my_amount = AmountOfMoney(IES_TOOL, iso_4217_currency_code_alpha3="CHF",amount=32.56)

    my_person.owns(my_amount)


    IES_TOOL.save_rdf("person3.ttl",rdf_format="ttl")


    # change the IES TOOL instance
    IES_TOOL = IESTool.get_instance(force_new=True)
    my_r = RdfsResource(tool=IES_TOOL)
    # my_person = IES_TOOL.create_person(given_name='Fred',
    #     surname='Smith',
    #     date_of_birth="1985-08-21",
    #     date_of_death="2024-01-01")
    my_person = IES_TOOL.create_person(
        given_name='Fred',
        surname='Smith',
        date_of_birth="1985-08-21",
        date_of_death="2024-01-01"
    )
    print(my_person.__dict__)

    IES_TOOL.save_rdf("person23.ttl",rdf_format="ttl")
