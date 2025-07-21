from rdflib import XSD, Graph, Literal, Namespace, URIRef

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

    def __init__(self):
        self.graph = Graph()
        self._supported_rdf_serialisations = ["turtle", "xml", "n3", "json-ld", "nt", "ttl", "ntriples"]
        self.warnings = []
        self.classes = set()
        self.properties = set()


    def set_classes(self, classes: set):
        self.classes = classes

    def set_properties(self, properties: set):
        self.properties = properties

    def clear_triples(self):
        if self.graph is not None:
            del self.graph
        self.graph = Graph()


    def get_rdf(self, rdf_format: str = None) -> str:
        return self.graph.serialize(format=rdf_format)

    def save_rdf(self,filename,rdf_format = None):
        with open(filename, "w") as text_file:
            text_file.write(self.get_rdf(rdf_format=rdf_format))

    def get_reporting(self) -> str:
        raise NotImplementedError

    def query_sp(self, subject: str, predicate: str) -> list:
        objs = []
        for s, p, o in self.graph.triples((URIRef(subject), URIRef(predicate), None)):
            objs.append(o.toPython())
            del s, p
        return objs

    def in_graph(self, subject: str, predicate: str, obj: str, is_literal: bool, literal_type: str = None) -> bool:
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

    def add_triple(self, subject: str, predicate: str, obj: str, is_literal: bool, literal_type: str = None):
        if not self.in_graph(
            subject=subject,
            predicate=predicate,
            obj=obj,
            is_literal=is_literal,
            literal_type=literal_type,
        ):

            if is_literal:
                try:
                    lt = getattr(XSD, literal_type)
                    rl_obj = Literal(obj, datatype=lt)
                except Exception:
                    rl_obj = Literal(obj)

            else:
                rl_obj = URIRef(obj)
            self.graph.add((URIRef(subject), URIRef(predicate), rl_obj))

    def can_validate(self) -> bool:
        return True

    def get_warnings(self) -> list[str]:
        return self.warnings

    def get_triple_count(self) -> int:
        return len(self.graph)

    def can_suppport_prefixes(self) -> bool :
        return True

    def add_prefix(self, prefix: str, uri: str) :
        self.graph.bind(prefix.replace(":", ""), Namespace(uri))

    @property
    def supported_rdf_serialisations(self) -> list:
        return self._supported_rdf_serialisations

    @property
    def deletion_supported(self) -> bool:
        return False
