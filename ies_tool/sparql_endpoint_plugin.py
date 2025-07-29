import requests
import shortuuid

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


class SPARQLEndpointPlugin:

    def __init__(
        self,
        default_data_namespace: str = "https://telicent.io/testdata#",
        server_host: str = "http://localhost:3030/",
        server_dataset: str = "ds",
        ser_user: str = "",
        server_password: str = "",
    ):
        self.default_data_namespace: str = default_data_namespace
        self.server_host: str = server_host
        self.server_dataset: str = server_dataset
        self.ser_user: str = ser_user
        self.server_password: str = server_password
        self._supported_rdf_serialisations = []
        try:
            query = "SELECT * WHERE { ?s ?p ?o } LIMIT 2"
            get_uri = self.server_host + self.server_dataset + "/query?query=" + query
            requests.get(get_uri)
        except ConnectionError as e:
            raise RuntimeError(
                f"Could not connect to SPARQL endpoint at {self.server_host}"
            ) from e

    def _run_sparql_update(self, query: str):
        """
        Executes a SPARQL update on a remote sparql server or rdflib - DOES NOT WORK ON plugins (yet)

        Args:
            query (str): The SPARQL query
            security_label (str): Security labels to apply to the data being created (this only applies
            if using Telicent CORE)
        """
        # This really needs updating to use the SPARQLWrapper library and Telicent CORE labels

        post_uri = f"{self.server_host}{self.server_dataset}/update"
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/sparql-update",
        }
        requests.post(post_uri, headers=headers, data=query)

    def _make_results_list_from_query(self, query: str, sparql_var_name: str) -> list:
        """
        Pulls out individual variable from each row returned from sparql query. It's a bit niche, I know.

        Args:
            query (str): The query
            sparql_var_name (str): The SPARQL var name
        """

        result_object = self._run_sparql_query(query)
        return_set = set()
        if (
            "results" in result_object.keys()
            and "bindings" in result_object["results"].keys()
        ):
            for binding in result_object["results"]["bindings"]:
                return_set.add(binding[sparql_var_name]["value"])
        return list(return_set)

    def _run_sparql_query(self, query: str) -> dict:
        """
        Runs a SPARQL query on the data

        Args:
            query (str): The query to run
        """

        get_uri = f"{self.server_host}{self.server_dataset}/query"
        response = requests.get(get_uri, params={"query": query})
        return response.json()

    @staticmethod
    def _prep_object(obj: str, is_literal: bool, literal_type: str) -> str:
        """
        Checks the type of object place in an RDF triple and formats it for use in a SPARQL query

        Args:
            obj (str) - the RDF object (third position in an RDF triple)
            is_literal (bool) - set to true if passing a literal object
            literal_type (str) - an XML schema datatype

        Returns:
            str: _description_
        """

        if is_literal:
            o = f'"{obj}"'
            if literal_type:
                o = f"{o}^^{literal_type}"
        else:
            o = f"<{obj}>"
        return o

    def _prep_spo(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool = True,
        literal_type: str | None = None,
    ) -> str:
        """
        Formats an RDF triple, so it can be used in a SPARQL query or update

        Args:
            subject - the first position of the triple
            predicate - the second position of the triple
            obj - the third position of the triple
            is_literal - set to true if the third position is a literal
            literal_type - if the third position is a literal, set its XML datatype
        """
        return f"<{subject}> <{predicate}> {self._prep_object(obj, is_literal, literal_type)}"

    def generate_data_uri(self, context: str | None = None) -> str:
        raise NotImplementedError

    def set_classes(self, classes: set):
        raise NotImplementedError

    def set_properties(self, properties: set):
        raise NotImplementedError

    def clear_triples(self):
        """Clears the current graph of all triples. Creates a new UUID for the session and resets the instance count.
        (as well as adding the default data namespace as a prefi into rdflib).
        """
        if hasattr(self, "graph") and self.graph is not None:
            del self.graph
        self.session_instance_count = 0
        self.uuid: str = shortuuid.uuid()
        self.warnings = []
        self.run_sparql_update("DELETE {?s ?p ?o .} WHERE {?s ?p ?o .}")

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
        # f"ASK {{ <> <>  {self._prep_object(obj, is_literal, literal_type)}}}"
        raise NotImplementedError

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_literal: bool,
        literal_type: str,
    ):
        triple = self._prep_spo(subject, predicate, obj, is_literal, literal_type)
        query = f"INSERT DATA {{{triple}}}"
        self._run_sparql_update(query=query)

    def can_validate(self) -> bool:
        raise NotImplementedError

    def get_warnings(self) -> list[str]:
        raise NotImplementedError

    def get_triple_count(self) -> int:
        raise NotImplementedError

    def can_suppport_prefixes(self) -> bool:
        return False

    def add_prefix(self, prefix: str, uri: str):
        raise NotImplementedError

    def get_namespace_uri(self, prefix: str) -> str:
        raise NotImplementedError

    @property
    def default_data_namespace(self):
        raise NotImplementedError

    @default_data_namespace.setter
    def default_data_namespace(self, value: str):
        raise NotImplementedError

    @property
    def supported_rdf_serialisations(self) -> list:
        raise NotImplementedError

    @property
    def deletion_supported(self) -> bool:
        raise NotImplementedError
