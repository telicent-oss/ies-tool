import logging
import inspect

from ies_tool import ies_classes

__license__ = """
Copyright TELICENT LTD

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

logger = logging.getLogger(__name__)
class RDFEntityFactory:
    def __init__(self, tool):
        self.module = ies_classes
        self.tool = tool
        self.class_map = self.build_class_map(self.module)

    def build_class_map(self, module):
        """
        Builds a case-insensitive class map from the given module, excluding specific classes.

        Args:
            module: The module from which to collect class definitions.

        Returns:
            dict: A dictionary mapping class names (in lower case) to class objects.
        Usage:
            tool = IESTool()
            factory = RDFEntityFactory(tool, ies_entities)
            # Creating an instance of Event dynamically, case-insensitive
            event = factory.create_entity('event', uri='http://example.com/events/1',
            event_start='2022-01-01T00:00:00Z')
        """
        class_map = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name != 'Unique':
                class_map[name.lower()] = obj

        logger.info('RDFEntity map initialised...')
        return class_map

    def create_entity(self, entity_class_name: str, **kwargs):
        """
        Create an entity by class name with provided kwargs, insensitive to case.

        Args:
            entity_class_name (str): The name of the class to instantiate, case-insensitive.
            **kwargs: Arbitrary keyword arguments for the entity creation.

        Returns:
            An instance of the specified class or raises ValueError if class not found.
        """
        entity_class = self.class_map.get(entity_class_name.lower())
        print(f"Requested entity={entity_class_name.lower()}, matched class={entity_class}")
        if entity_class is None:
            raise ValueError(f"No such class: {entity_class_name}")
        return entity_class(tool=self.tool, **kwargs)
