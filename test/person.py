import time
from unittest import TestCase
from unittest.mock import mock_open, patch

from ies_tool.ies_tool import Element, Entity, IESTool, Person

tool = IESTool(validate=True)

my_person = Person(
    tool=tool,
    given_name='Fred',
    family_name='Smith',
    date_of_birth="1985-08-21"
)

tool.save_rdf('./person.ttl', format="ttl")
