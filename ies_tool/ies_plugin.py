import ies_tool.ies_constants as ies_constants

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


class IESPlugin:
    """
    Abstract base class for IES storage plugins.
    """

    def __init__(self, default_data_namespace: str = ies_constants.DEFAULT_DATA_NAMESPACE):
        self._default_data_namespace = default_data_namespace

    def generate_data_uri(self, context: str | None = None) -> str:
        raise NotImplementedError

    def set_classes(self, classes: set):
        raise NotImplementedError

    def set_properties(self, properties: set):
        raise NotImplementedError

    def clear_triples(self):
        raise NotImplementedError

    def get_rdf(self, rdf_format: str = None) -> str:
        raise NotImplementedError

    def save_rdf(self, filename, rdf_format=None):
        raise NotImplementedError

    def query_sp(self, subject: str, predicate: str) -> list:
        raise NotImplementedError

    def in_graph(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool,
        literal_type: str = None,
    ) -> bool:
        raise NotImplementedError

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool,
        literal_type: str,
    ):
        raise NotImplementedError

    def can_validate(self) -> bool:
        raise NotImplementedError

    def get_warnings(self) -> list[str]:
        raise NotImplementedError

    def get_triple_count(self) -> int:
        raise NotImplementedError

    def can_support_prefixes(self) -> bool :
        raise NotImplementedError

    def add_prefix(self, prefix: str, uri: str):
        raise NotImplementedError

    def get_namespace_uri(self, prefix: str) -> str:
        raise NotImplementedError

    @property
    def default_data_namespace(self):
        return self._default_data_namespace

    @default_data_namespace.setter
    def default_data_namespace(self, value: str):
        self._default_data_namespace = value

    @property
    def supported_rdf_serialisations(self) -> list:
        raise NotImplementedError

    @property
    def deletion_supported(self) -> bool:
        raise NotImplementedError
