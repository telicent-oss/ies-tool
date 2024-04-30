import datetime as dt
from ies_tool.ies_classes import Event, PERSON, Person, EVENT

class RDFEntityFactory:
    def __init__(self, tool):
        self.tool = tool

    def create_event(self, **kwargs) -> Event:
        if kwargs['classes'] is None:
            kwargs['classes'] = [EVENT]
        return Event(tool=self.tool, **kwargs)


    def create_person(self, **kwargs):
        if kwargs.get('classes') is None:
            classes = [PERSON]

        person = Person(tool=self.tool, **kwargs)

        return person