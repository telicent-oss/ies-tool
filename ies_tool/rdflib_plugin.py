import shortuuid
from rdflib import XSD, Graph, Literal, Namespace, URIRef
from rdflib.namespace import NamespaceManager

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


class RdfLibPlugin:

    def __init__(self, default_data_namespace: str = ies_constants.DEFAULT_DATA_NAMESPACE):
        """Creates an instance of the RdfLibPlugin class - a serialisation plugin that uses rdflib to manage RDF data.

        Args:
            default_data_namespace: The default URI namespace for generated data.
        """
        self._supported_rdf_serialisations = [
            "turtle",
            "xml",
            "n3",
            "json-ld",
            "nt",
            "ttl",
            "ntriples",
        ]
        self._default_data_namespace = default_data_namespace
        self.classes = set()
        self.properties = set()
        self.clear_triples()

    def generate_data_uri(self, context: str | None = None) -> str:
        """
        Creates a random (UUID) appended to the default data namespace in use

        Args:
            context (str): an additional string to insert into the URI to provide human-readable context
        """
        if context is None:
            context = ""
        uri = f"{self._default_data_namespace}{self.uuid}{context}_{self.session_instance_count}"
        self.session_instance_count = self.session_instance_count + 1
        return uri

    def set_classes(self, classes: set):
        """Allows the plugin to store a set of allowable RDFS/OWL classes.

        Args:
            classes (set): _description_
        """
        self.classes = classes

    def set_properties(self, properties: set):
        """Allows the plugin to store a set of allowable RDFS/OWL properties.

        Args:
            properties (set): _description_
        """
        self.properties = properties

    def clear_triples(self):
        """Clears the current graph of all triples. Creates a new UUID for the session and resets the instance count.
        (as well as adding the default data namespace as a prefi into rdflib).
        """
        if hasattr(self, "graph") and self.graph is not None:
            del self.graph
        self.graph = Graph()
        self.namespace_manager = NamespaceManager(self.graph)
        self.session_instance_count = 0
        self.uuid: str = shortuuid.uuid()
        self.add_prefix(":", self._default_data_namespace)
        self.warnings = []

    def get_rdf(self, rdf_format: str = None) -> str:
        """Returns the current graph in the specified RDF format.

        Args:
            rdf_format (str, optional): _description_. Defaults to None.

        Returns:
            str: _description_
        """
        return self.graph.serialize(format=rdf_format)

    def save_rdf(self, filename, rdf_format=None):
        """Saves the current graph to a file in the specified RDF format.

        Args:
            filename (_type_): _description_
            rdf_format (_type_, optional): _description_. Defaults to None.
        """
        with open(filename, "w") as text_file:
            text_file.write(self.get_rdf(rdf_format=rdf_format))

    def query_sp(self, subject: str, predicate: str) -> list:
        """Queries the current graph for all objects that match the given subject and predicate.

        Args:
            subject (str): _description_
            predicate (str): _description_

        Returns:
            list: the object URIs
        """
        objs = []
        for s, p, o in self.graph.triples((URIRef(subject), URIRef(predicate), None)):
            objs.append(o.toPython())
            del s, p
        return objs

    def in_graph(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool,
        literal_type: str = None,
    ) -> bool:
        """
        Checks to see if we already have a triple in the current graph

        Args:
            subject (str): The subject (first position) of the triple to check
            predicate (str): The predicate (second position))
            obj (str): The object (third position)
            is_literal (bool): Whether to the object of the triple is a literal
            literal_type (str): If the object is a literal, what datatype to look for

        Returns:
            bool: Whether the triple is in the graph of not
        """
        if is_literal:
            return (URIRef(subject), URIRef(predicate), Literal(obj)) in self.graph
        else:
            return (URIRef(subject), URIRef(predicate), URIRef(obj)) in self.graph

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool,
        literal_type: str = None,
    ):
        """Adds a triple to the current graph if it does not already exist.

        Args:
            subject (str): the subject of the triple (first position)
            predicate (str): the predicate of the triple (second position)
            obj (str): the object of the triple (third position) - may be a URI or a literal
            is_literal (bool): is the object of the triple a literal ?
            literal_type (str, optional): Optional RDF literal datatype if the object is a literal. Defaults to None.
        """
        if not self.in_graph(
            subject=subject,
            predicate=predicate,
            obj=obj,
            is_literal=is_literal,
            literal_type=literal_type,
        ):

            if is_literal:
                if literal_type is None or literal_type == "":
                    rl_obj = Literal(obj)
                else:
                    if (
                        literal_type == "string"
                    ):  # catching legacy IES_TOOL literal type
                        rl_obj = Literal(obj, datatype=XSD.string)
                    else:
                        rl_obj = Literal(obj, datatype=URIRef(literal_type))

            else:
                rl_obj = URIRef(obj)
            self.graph.add((URIRef(subject), URIRef(predicate), rl_obj))

    def can_validate(self) -> bool:
        """Indicates if validation is supported by this plugin.

        Returns:
            bool: _description_
        """
        return True

    def get_warnings(self) -> list[str]:
        """returns a list of warnings generated by the plugin during processing.

        Returns:
            list[str]: _description_
        """
        return self.warnings

    def get_triple_count(self) -> int:
        """Returns the number of triples currently in the graph.

        Returns:
            int: _description_
        """
        return len(self.graph)

    def can_suppport_prefixes(self) -> bool:
        """Indicates if the plugin can support prefixes in the RDF graph.

        Returns:
            bool: _description_
        """
        return True

    def add_prefix(self, prefix: str, uri: str):
        """Adds a prefix to the namespace manager for the graph.

        Args:
            prefix (str): _description_
            uri (str): _description_
        """
        self.namespace_manager.bind(prefix.replace(":", ""), Namespace(uri))

    def get_namespace_uri(self, prefix: str) -> str:
        """
        Get the namespace for a given prefix.

        Args:
            prefix (str): The prefix to get the namespace for.

        Returns:
            Namespace: The namespace associated with the prefix.
        """
        return self.namespace_manager.store.namespace(
            prefix.replace(":", "")
        ).toPython()

    @property
    def default_data_namespace(self):
        """Returns the default data namespace currently in use.

        Returns:
            _type_: _description_
        """
        return self._default_data_namespace

    @default_data_namespace.setter
    def default_data_namespace(self, value: str):
        """Sets the default data namespace for the plugin and adds it as a prefix.

        Args:
            value (str): _description_
        """
        self._default_data_namespace = value
        self.add_prefix(":", self.default_data_namespace)

    @property
    def supported_rdf_serialisations(self) -> list:
        """Returns a list of supported RDF serialisations by the plugin.

        Returns:
            list: _description_
        """
        return self._supported_rdf_serialisations

    @property
    def deletion_supported(self) -> bool:
        """Indicates if the plugin supports deletion of triples.

        Returns:
            bool: _description_
        """
        return False
