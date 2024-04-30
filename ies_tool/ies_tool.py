from __future__ import annotations
import io
import json
import logging
import os
import pathlib
import uuid
import warnings
import threading

import iso4217parse
import phonenumbers
import pycountry
import requests
import validators
import validators.uri
from geohash_tools import encode
from pyshacl import validate as pyshacl_validate
from rdflib import XSD, Graph, Literal, Namespace, URIRef

from typing import TypeVar

from ies_tool.ies_ontology import IES_BASE, Ontology
from ies_tool.ies_plugin import IESPlugin
from ies_tool.utils import RDFEntityFactory


# todo Remove after deprication cleanup
from ies_tool.ies_classes import *
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

DEFAULT_PREFIXES = {
    "xsd:": "http://www.w3.org/2001/XMLSchema#",
    "dc:": "http://purl.org/dc/elements/1.1/",
    "rdf:": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs:": "http://www.w3.org/2000/01/rdf-schema#",
    "owl:": "http://www.w3.org/2002/07/owl#",
    "iso8601:": "http://iso.org/iso8601#",
    "iso3166:": "http://iso.org/iso3166#",
    "iso4217:": "http://iso.org/iso4217#",
    "tont:": "http://telicent.io/ontology/",
    "e164:": "https://www.itu.int/e164#",
    "IMSI:": "https://www.itu.int/e212#",
    "rfc5322:": "https://ietf.org/rfc5322#",
    "ieee802:": "https://www.ieee802.org#",
    "ies:": IES_BASE
}


class IESTool:
    """
    IESTool is a Python library for working with the UK Government Information Exchange Standard. This is the main class
    you need to initialise to start creating IES RDF data. The IESTool class acts as a factory for classes, and holds
    the created RDF instances.

    Once created, and IESTool object can be used over and over again for creating new IES files. Simply clear_graph()
    between file creation runs rather than initiating a new IESTool object (which carries some overhead and delay)

    Instances of the IESTool class hold an in-memory copy of the IES ontology in a
    [rdflib](https://github.com/RDFLib/rdflib) graph which can be accessed through self.ontology.graph

    IESTool can work with in-memory data (e.g. with rdflib) or can connect to a SPARQL compliant triplestore and
    manipulate data in that dataset.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(
            self, default_data_namespace: str = "http://example.com/rdf/testdata#", mode: str = "rdflib",
            plug_in: IESPlugin | None = None, validate: bool = False, server_host: str = "http://localhost:3030/",
            server_dataset: str = "ds", default_security_label: str | None = None
    ):
        """

        Args:
            default_data_namespace (str): The default URI path used for generating node URIs
            mode (str):
                The mode that the tool should run in. Should be one of:
                    - rdflib (default) - slow, but includes a lot of RDF checking. Ideal for dev and testing
                    - sparql_server - connects to a remote triplestore. Use with care !
                    - plugin - you can develop your own storage engine and plug it in
            plug_in (IESPlugin):
                if the mode param is "plugin", IES Tool will expect you to provide a compliant storage plug_in
                (see example class in ies_plugin.py)
            validate (bool):
                if in rdflib mode and if validate is true, IES Tool will check the data you create against the IES
                SHACL patterns
            server_host (str):
                For use in sparql_server mode, the host URI of the triplestore
            server_dataset (str):
                For use in sparql_server mode, the name of the triplestore dataset you want to work on
        """
        with self.__class__._lock:
            # The following check ensures that initialization only happens once.
            if not hasattr(self, '_initialized'):
                # Perform initialization here.
                self.instances: dict = {}
                # Lookup for XSD datatypes
                self.xsdDatatypes = [
                    "string",  # Character strings (but not all Unicode character strings)
                    "boolean",  # true / false
                    "decimal",  # Arbitrary-precision decimal numbers
                    "integer",  # Arbitrary-size integer numbers
                    "double",  # 64-bit floating point numbers incl. ±Inf, ±0, NaN
                    "float",  # 32-bit floating point numbers incl. ±Inf, ±0, NaN
                    "date",  # Dates (yyyy-mm-dd) with or without timezone
                    "time",  # Times (hh:mm:ss.sss…) with or without timezone
                    "dateTime",  # Date and time with or without timezone
                    "dateTimeStamp",  # Date and time with required timezone
                    "gYear",  # Gregorian calendar year
                    "gMonth",  # Gregorian calendar month
                    "gDay",  # Gregorian calendar day of the month
                    "gYearMonth",  # Gregorian calendar year and month
                    "gMonthDay",  # Gregorian calendar month and day
                    "duration",  # Duration of time
                    "yearMonthDuration",  # Duration of time (months and years only)
                    "dayTimeDuration",  # Duration of time (days, hours, minutes, seconds only)
                    "byte",  # -128…+127 (8 bit)
                    "short",  # -32768…+32767 (16 bit)
                    "int",  # -2147483648…+2147483647 (32 bit)
                    "long",  # -9223372036854775808…+9223372036854775807 (64 bit)
                    "unsignedByte",  # 0…255 (8 bit)
                    "unsignedShort",  # 0…65535 (16 bit)
                    "unsignedInt",  # 0…4294967295 (32 bit)
                    "unsignedLong",  # 0…18446744073709551615 (64 bit)
                    "positiveInteger",  # Integer numbers >0
                    "nonNegativeInteger",  # Integer numbers ≥0
                    "negativeInteger",  # Integer numbers <0
                    "nonPositiveInteger",  # Integer numbers ≤0
                    "hexBinary",  # Hex-encoded binary data
                    "base64Binary",  # Base64-encoded binary data
                    "anyURI",  # Absolute or relative URIs and IRIs
                    "language",  # Language tags per [BCP47]
                    "normalizedString",  # Whitespace-normalized strings
                    "token",  # Tokenized strings
                    "NMTOKEN",  # XML NMTOKENs
                    "Name",  # XML Names
                    "NCName"
                ]
                # Initiate the storage plugins dictionary
                self.plug_in: IESPlugin | None = None

                # Property initialisations

                self.session_instance_count = None
                self.session_uuid_str = None
                self.session_uuid = None
                self.current_dir = pathlib.Path(__file__).parent.resolve()

                local_folder = os.path.dirname(os.path.realpath(__file__))
                ont_file = os.path.join(local_folder, "ies4.ttl")
                self.ontology = Ontology(ont_file)

                self.__mode = mode
                if mode not in ["rdflib", "sparql_server"]:
                    self._register_plugin(mode, plug_in)

                if self.__mode == "plugin":
                    logger.info("Using a user-defined storage plugin")
                    if validate:
                        logger.warning("IES Tool cannot validate unless in 'rdflib' mode")
                        self.__validate = False
                elif mode == "rdflib" and validate:
                    if not validate:
                        logger.warning('Enabling validation for rdflib mode')
                    self.__validate = True
                    self._init_shacl(os.path.join(self.current_dir, "ies_r4_2_0.shacl"))
                    logger.info("IES Tool set to validate all messages. This might get a bit slow")
                elif mode == "sparql_server":
                    self.server_host = server_host
                    self.server_dataset = server_dataset
                    self.default_security_label = default_security_label or ""
                    try:
                        query = "SELECT * WHERE { ?s ?p ?o } LIMIT 2"
                        get_uri = self.server_host + self.server_dataset + "/query?query=" + query
                        requests.get(get_uri)
                    except ConnectionError as e:
                        raise RuntimeError(f"Could not connect to SPARQL endpoint at {self.server_host}") from e

                logger.debug("initialising data graph")

                # Note that both plugin and rdflib datasets are initialised to enable quick changeover
                self.graph = Graph()

                self.prefixes: dict[str, str] = {}
                self.default_data_namespace = default_data_namespace

                # Establish a set of useful prefixes
                for k, v in DEFAULT_PREFIXES.items():
                    self.add_prefix(k, v)

                if self.__mode != "sparql_server":
                    self.clear_graph()

                self.ies_namespace = IES_BASE
                self.iso8601_namespace = "http://iso.org/iso8601#"
                self.rdf_type = f"{self.prefixes['rdf:']}type"
                self.rdfs_resource = f"{self.prefixes['rdfs:']}Resource"
                self.rdfs_comment = f"{self.prefixes['rdfs:']}comment"
                self.rdfs_label = f"{self.prefixes['rdfs:']}label"

                self.__validate = False

                # Create a layered dictionary of base classes, along with their corresponding IES subclasses.
                # This enables look up of most appropriate base class when call instantiate
                # This may be better if it was in the ies_ontology library, but they don't have access to
                # the class definitions and didn't want to create a circular dependency...again
                self.base_classes = self._all_python_subclasses({}, RdfsResource, 0)
                # Set the _initialized flag so that we don't initialize it again.
                self._initialized = True

    @staticmethod
    def get_instance():
        return IESTool()

    @property
    def default_data_namespace(self):
        return self.prefixes[":"]

    @property
    def entity_factory(self):
        return RDFEntityFactory(self.get_instance())

    @default_data_namespace.setter
    def default_data_namespace(self, value):
        self.add_prefix(":", value)

    def add_prefix(self, prefix: str, uri: str):
        """
        Adds an RDF prefix to the internal list of namespace prefixes. If using rdflib for the in-memory graph,
        it will also register the namespace there.

        Note that if the prefix is an empty string or ':' it will set the default_data_namespace for the
        IESTool instance.

        Args:
            prefix (str): The prefix to add
            uri (str): The corresponding namespace URI
        """

        if ":" not in prefix:
            prefix = prefix + ":"

        self.prefixes[prefix] = uri
        if self.__mode == "rdflib":
            ns = Namespace(uri)
            self.graph.bind(prefix.replace(":", ""), ns)

    def _mint_dependent_uri(self, parent_uri: str, postfix: str) -> str:
        new_uri = f'{parent_uri}_{postfix}_001'
        counter = 1
        while new_uri in self.instances:
            counter += 1
            new_uri = f'{parent_uri}_{postfix}_{counter:03d}'
        return new_uri

    def format_prefixes(self) -> str:
        """
        Returns the prefixes held in IESTool, formatted for use in SPARQL queries

        Returns:
            str: The formatted prefixes
        """

        prefix_str = ''
        for prefix in self.prefixes:
            prefix_str = f"{prefix_str}PREFIX {prefix} <{self.prefixes[prefix]}> "
        return prefix_str

    def _all_python_subclasses(self, hierarchy: dict, cls: Unique, level: int) -> dict:
        """_summary_

        Args:
            hierarchy (dict): _description_
            cls (Unique): _description_
            level (int): _description_

        Returns:
            dict: _description_
        """
        if level not in hierarchy:
            hierarchy[level] = {}
        uri = ''
        if "Rdfs" in cls.__name__:
            uri = cls.__name__.replace("Rdfs", RDFS)
        else:
            uri = IES_BASE + cls.__name__
        ies_subs = self.ontology.make_results_set_from_query(
            "SELECT ?p WHERE {?p <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + uri + ">}", "p")
        hierarchy[level][uri] = {'python_class': cls, 'ies_subclasses': list(ies_subs)}
        subclasses = cls.__subclasses__()
        if len(subclasses) > 0:
            for sub in subclasses:
                self._all_python_subclasses(hierarchy, sub, level + 1)
        return hierarchy

    # Given an IES or RDFS class, this function will attempt to return the most appropriate base class
    # (and its level identifier)
    def _determine_base_class(self, classes):
        keys = reversed(self.base_classes.keys())
        for level_number in keys:
            level = self.base_classes[level_number]
            for bc in level:
                base_class = level[bc]
                for cls in classes:
                    if cls in base_class['ies_subclasses']:
                        return base_class["python_class"], level_number

        return self.base_classes[0]["python_class"], 0

    def get_obj_instance(self, from_type: str | RdfsResource, to_type: object | None = None,
                         context: str | None = None):
        """
        Gets an instance (by its URI) that has already been created in this session. Note if you are connected to a
        remote SPARQL server or have loaded data into in-memory graph, pre-existing instances will not have been
        cached by the IESTool.

        Args:
            from_type (str | obj): The URI
            to_type (obj): Type to map to
            context (str): Debugging purposes


        Returns:
           Reference to an instance
        """
        logger.debug(f"Getting object instance {from_type=}, {to_type=}, {context=}")
        to_type = to_type or RdfsResource
        if isinstance(from_type, str):
            return self.instances.get(from_type, to_type(self, uri=from_type, classes=[]))

        return self.instances.get(from_type.uri, to_type(self, uri=from_type.uri, classes=[]))

    def _register_plugin(self, plugin_name: str, plugin: IESPlugin):
        """
        Registers a plugin after initialisation.

        Args:
            plugin_name (str): The plugin to register
            plugin (IESPlugin): The plugin
        """

        if plugin is None:
            raise RuntimeError("No plugin provided")
        elif plugin_name == "rdflib":
            raise RuntimeError("'rdflib' is a reserved name")
        elif plugin_name == "sparql_server":
            raise RuntimeError("'sparql_server' is a reserved name")
        else:
            setattr(self, 'plug_in', plugin)
            self.plug_in.set_classes(self.ontology.classes)
            self.plug_in.set_properties(self.ontology.properties)

    def _init_shacl(self, shacl_filename: str):
        """Loads SHACL shapes for validation

        Args:
            shacl_filename (str): the shacl file to use
        """
        logger.info("parsing SHACL rules")
        self.shacl = Graph()
        self.shacl.parse(shacl_filename)
        logger.info("SHACL ready")

    def clear_graph(self) -> uuid.UUID:
        """
        Clears the graph currently in use. This is the quickest way to run repeated IES data runs - far quicker
        than constantly initiating new IESTool objects

        Returns:
            uuid.UUID: The session uuid.
        """

        if self.__mode == "plugin":
            self.plug_in.clear_triples()
        elif self.__mode == "sparql_server":
            self.run_sparql_update("DELETE {?s ?p ?o .} WHERE {?s ?p ?o .}")
        else:
            if self.graph is not None:
                del self.graph
            self.graph = Graph()
            for prefix in self.prefixes:
                self.graph.bind(prefix.replace(":", ""), self.prefixes[prefix])
        self.session_uuid = uuid.uuid4()
        self.session_uuid_str = self.session_uuid.hex
        self.session_instance_count = 0
        self.instances = {}
        return self.session_uuid

    def run_sparql_update(self, query: str, security_label: str | None = None):
        """
        Executes a SPARQL update on a remote sparql server or rdflib - DOES NOT WORK ON plugins (yet)

        Args:
            query (str): The SPARQL query
            security_label (str): Security labels to apply to the data being created (this only applies
            if using Telicent CORE)
        """

        if self.__mode == "sparql_server":
            if security_label is None:
                security_label = self.default_security_label
            post_uri = f"{self.server_host}{self.server_dataset}/update"
            headers = {
                'Accept': '*/*',
                'Security-Label': security_label,
                'Content-Type': 'application/sparql-update'
            }
            requests.post(post_uri, headers=headers, data=f"{self.format_prefixes()}{query}")
        elif self.__mode == "rdflib":
            self.graph.update(f"{self.format_prefixes()}{query}")
        else:
            raise RuntimeError(
                f"Cannot issue SPARQL Update unless using rdflib or remote sparql. You are using {self.__mode}"
            )

    def make_results_list_from_query(self, query: str, sparql_var_name: str) -> list:
        """
        Pulls out individual variable from each row returned from sparql query. It's a bit niche, I know.

        Args:
            query (str): The query
            sparql_var_name (str): The SPARQL var name
        """

        result_object = self.run_sparql_query(query)
        return_set = set()
        if "results" in result_object.keys() and "bindings" in result_object["results"].keys():
            for binding in result_object["results"]['bindings']:
                return_set.add(binding[sparql_var_name]['value'])
        return list(return_set)

    def run_sparql_query(self, query: str) -> dict:
        """
        Runs a SPARQL query on the data - DOES NOT WORK ON plugins (yet)

        Args:
            query (str): The query to run
        """

        if self.__mode == "sparql_server":
            get_uri = f"{self.server_host}{self.server_dataset}/query"
            response = requests.get(get_uri, params={'query': f"{self.format_prefixes()}{query}"})
            return response.json()
        elif self.__mode == "rdflib":
            self.graph.query(f"{self.format_prefixes()}{query}")
            with io.StringIO() as f:
                return json.loads(f.getvalue())
        else:

            raise RuntimeError(
                f"Cannot issue SPARQL Query unless using rdflib or remote sparql. You are using {self.__mode}"

            )

    @staticmethod
    def _str(_input: str | Graph) -> str:
        """
        Designed to catch iffy datatypes being passed in (e.g. legacy rdflib types)

        Args:
            _input (str | Graph):
        """
        if isinstance(_input, str):
            return _input
        elif isinstance(_input, RdfsResource):
            return _input.uri
        elif isinstance(_input, float) or isinstance(_input, int):
            return str(_input)
        else:
            try:
                output = _input.toPython()
                warnings.warn(
                    f"Triple component {output} is not a string, use of rdflib types is deprecated, please use strings",
                    DeprecationWarning,
                    stacklevel=2
                )
                return output
            except Exception as e:
                raise RuntimeError(f"Cannot create a triple where one place is of type {str(_input)}") from e

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
                o = f'{o}^^{literal_type}'
        else:
            o = f'<{obj}>'
        return o

    def _prep_spo(self, subject: str, predicate: str, obj: str, is_literal: bool = True,
                  literal_type: str | None = None) -> str:
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

    def switch_mode(self, mode: str):
        """
        Switches between rdflib and plugin modes - note this also clears the graph.

        Args:
            mode (str): The mode to switch to
        """
        if mode not in ["rdflib", "plugin"]:
            raise RuntimeError("Unknown mode: {mode}")
        else:
            self.__mode = mode
            self.clear_graph()

    def get_rdf(self, rdf_format: str = "nt", clear: bool = False) -> dict:
        """
        Returns the RDF in the format requested embedded in a dictionary.
        Note this only applies if in rdflib mode, or if the storage plugin supports data export

        Args:
            rdf_format (str): The requested rdf format (default is "nt" for n-triples)
            clear (bool): Whether to clear the graph after export of the data
        :return:
        """

        ret_dict: dict[str, str | list] = {
            "session_uuid": self.session_uuid,
            "triples": "",
            "validation_errors": "",
            "warnings": [],
        }
        if self.__mode == "plugin":
            if rdf_format not in self.plug_in.supported_rdf_serialisations:
                logger.warning(
                    f"Current plugin only supports {str(self.plug_in.supported_rdf_serialisations)}"
                    f" - you tried to export as {rdf_format}"
                )
            ret_dict["triples"] = self.plug_in.get_rdf()
            ret_dict["warnings"].extend(self.plug_in.get_warnings())
            if clear:
                self.clear_graph()
        if self.__mode == "sparql_server":
            logger.warning("Export RDF not supported in sparql server mode")
        else:
            if self.__validate:
                r = pyshacl_validate(
                    self.graph,
                    shacl_graph=self.shacl,
                    ont_graph=self.ontology.graph,
                    inference='rdfs',
                    abort_on_first=True,
                    allow_infos=False,
                    allow_warnings=False,
                    meta_shacl=False,
                    advanced=False,
                    js=False,
                    debug=False
                )
                conforms, results_graph, results_text = r
                if not conforms:
                    ret_dict["validation_errors"] = results_text
            ret_dict["triples"] = self.graph.serialize(format=rdf_format)
            if clear:
                self.clear_graph()
        return ret_dict

    def save_rdf(self, filename, rdf_format: str = "nt", clear: bool = False):
        """
        Saves the data in the chosen RDF forma

        Args:
            filename (str): The full file name to write out to
            rdf_format (str): The format of the saved RDF (default is "nt" for n-triples)
            clear (bool): Whether to clear the graph after saving
        """

        with open(filename, "w") as text_file:
            ret_dict = self.get_rdf(rdf_format=rdf_format, clear=clear)
            text_file.write(ret_dict["triples"])
            logger.info(f"File written: {filename}")

    def in_graph(
            self, subject: str, predicate: str, obj: str, is_literal: bool = False, literal_type: str = "string"
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

        if self.__mode == "plugin":
            return self.plug_in.in_graph(subject, predicate, obj, is_literal=is_literal)
        elif self.__mode == "sparql_server":
            f'ASK {{ <> <>  {self._prep_object(obj, is_literal, literal_type)}}}'
        else:
            if is_literal:
                return (URIRef(subject), URIRef(predicate), Literal(obj)) in self.graph
            else:
                return (URIRef(subject), URIRef(predicate), Literal(obj)) in self.graph

    def generate_data_uri(self, context: str | None = None) -> str:
        """
        Creates a random (UUID) appended to the default data namespace in use

        Args:
            context (str): an additional string to insert into the URI to provide human-readable context
        """
        if context is None:
            context = ""
        uri = f'{self.default_data_namespace}{self.session_uuid_str}{context}_{self.session_instance_count:06d}'
        self.session_instance_count = self.session_instance_count + 1
        return uri

    def delete_triple(self, subject: str, predicate: str, obj: str, is_literal: bool = False) -> bool:
        """
        Removes a triple from a graph when provided with subject, predicate and object as strings
        If removing a literal triple, set the is_literal to True
        This function expects strings, but will also try to fix things if you provide a URIRef of Literal.
        Please provide strings though. Thanks.

        Args:
            subject (str): The subject (first position) of the triple to be removed
            predicate (str): The predicate (second position) of the triple to be removed
            obj (str): The object (third position) of the triple to be removed
            is_literal (bool): Whether the object is a literal

        Returns:
            bool: Returns true if the update has executed. This does not guarantee the data was deleted though.
        """

        if self.__mode == "plugin" and not self.plug_in.deletion_supported:
            logger.warning("Triple deletion not currently supported in plugin")
        else:
            update = f'DELETE DATA {{{self._prep_spo(subject, predicate, obj, is_literal)}}}'
            self.run_sparql_update(update)
        return True

    def add_to_graph(self, subject: str, predicate: str, obj: str, is_literal: bool = False,
                     literal_type: str = "string", security_label: str | None = None) -> bool:
        """DEPRECATED - use add_triple()

        Args:
            subject (str): _description_
            predicate (str): _description_
            obj (str): _description_
            is_literal (bool, optional): _description_. Defaults to False.
            literal_type (str, optional): _description_. Defaults to "string".
            security_label (str, optional): _description_. Defaults to "".

        Returns:
            bool: _description_
        """
        warnings.warn("add_to_graph() is deprecated - please use add_triple()",
                      DeprecationWarning, stacklevel=2)
        return self.add_triple(subject=subject, predicate=predicate, obj=obj, is_literal=is_literal,
                               literal_type=literal_type, security_label=security_label)

    def add_triple(self, subject: str, predicate: str, obj: str, is_literal: bool = False,
                   literal_type: str = "string", security_label: str | None = None) -> bool:
        """
        Adds a triple to a graph when provided with subject, predicate and object as strings
        If setting a literal triple, set the is_literal to True
        This function expects strings, but will also try to fix things if you provide a rdflib URIRef of Literal.
        Please provide strings though. Thanks.

        Args:
            subject (str): The subject of the triple to add
            predicate (str): The predicate of the triple to add
            obj (str): The object of the triple to add
            is_literal (bool): Whether to check a literal or not
            literal_type (str): The type of literal
            security_label (str): Security label to apply

        Returns:
            bool: If the update ran. SPARQL endpoints do not confirm addition though, so check dataset after use
        """

        if security_label is None:
            security_label = ""

        if self.__mode == "plugin":
            self.plug_in.add_triple(
                subject=subject, predicate=predicate, obj=obj, is_literal=is_literal, literal_type=literal_type
            )
            return True
        elif self.__mode == "sparql_server":
            triple = self._prep_spo(subject, predicate, obj, is_literal, literal_type)
            query = f'INSERT DATA {{{triple}}}'
            self.run_sparql_update(query=query, security_label=security_label)
        elif not self.in_graph(
                subject=subject, predicate=predicate, obj=obj, is_literal=is_literal, literal_type=literal_type
        ):
            # See is someone has passed a rdflib type and fix it
            subject = self._str(subject)
            predicate = self._str(predicate)
            obj = self._str(obj)

            # Send out a warning if a non-IES predicate is used
            if is_literal:
                if predicate not in self.ontology.datatype_properties:
                    logger.warning(f"non-IES datatype property used: {predicate}")
            else:
                if predicate not in self.ontology.object_properties:
                    logger.warning(f"non-IES object property used: {predicate}")

            if is_literal:
                try:
                    lt = getattr(XSD, literal_type)
                except AttributeError:
                    lt = XSD.string
                obj = Literal(obj, datatype=lt)
            else:
                obj = URIRef(obj)
            self.graph.add((URIRef(subject), URIRef(predicate), obj))

    def add_literal_property(self, subject: str, predicate: str, obj: str, literal_type: str = "string") -> bool:
        """
        Adds a triple where the object is a literal

        Args:
            subject (str): The subject of the triple to add
            predicate (str): The predicate of the triple to add
            obj (str): The object of the triple to add
            literal_type: the XML datatype to use (default is "string")
        """
        return self.add_triple(subject, predicate, obj, is_literal=True, literal_type=literal_type)

    def instantiate(self, classes: list | None = None, uri: str = None, instance_uri_context: str | None = None,
                    base_class: RdfsResource | None = None) -> RdfsResource:
        """
        Instantiates a list of classes

        Args:
            classes (list | None): The classes to instantiate (a single instance, of multiple classes).
            uri (str): The URI of the instance (if not set, one will be generated)
            instance_uri_context (str): an additional string to insert into the URI to provide human-readable
            context if no URI is provided
            base_class (RdfsResource): The base Python class to use (default is RdfsResource)
        """

        if instance_uri_context is None:
            instance_uri_context = ""

        if not classes:
            classes = [RDFS_RESOURCE]

        if not isinstance(classes, list):
            raise RuntimeError(
                "instaniate() expects a list of classes - if you want to instantiate just one class,"
                " make a singleton list"
            )
        if base_class is None:
            base_class, level = self._determine_base_class(classes)

        if uri is None:
            # Make an uri based on the data stub...
            uri = self.generate_data_uri(instance_uri_context)

        cls_str: str = ""
        classes.sort()

        # If we have more than one class, we make a new class name by concatenating the class names
        for cls in classes:
            cls_name = cls.replace(self.ies_namespace, "")
            cls_str = f"{cls_str}{cls_name}"

        return base_class(uri=uri, tool=self, classes=classes)

    def create_event(self, uri: str | None = None, classes: list | None = None,
                     event_start: str | None = None, event_end: str | None = None,
                     ) -> Event:
        """
        DEPRECATED - use Event() to instantiate an IES Event.

        Args:
            uri (str): The URI for the event
            classes (list): a list of IES classes that it will be a member of
            event_start (str): The start of the event as an ISO8601 string (no spaces - use a T)
            event_end (str): The end of the event as an ISO8601 string (no spaces - use a T)

        Returns:
            Event: The created Event wrapped as an IES Event class
        """
        warnings.warn("IESTool.create_event is deprecated - please initiate Event Python class directly",
                      DeprecationWarning, stacklevel=2)
        kwargs = locals()
        del kwargs['self']
        return self.entity_factory.create_event(**kwargs)

    def create_person(self, uri: str | None = None, classes: list | None = None,
                      given_name: str | None = None, surname: str | None = None, date_of_birth: str | None = None,
                      place_of_birth: LocationType | None = None, date_of_death: str | None = None,
                      place_of_death: LocationType | None = None) -> PersonType:
        """
        DEPRECATED - use Person() to instantiate an IES Person

        Args:
            given_name (str): first name of the person
            surname (str): surname of the person
            date_of_birth (str): date of birth of the person (ISO8601 string, no spaces, use T)
            place_of_birth (Location): place of birth of the person a Python Location object
            classes (list): the IES types to instantiate  - default is Person - shouldn't need to change this
            uri (str): the URI of the Person instance - if unset, one will be created.
            date_of_death (str): date of death of the person (ISO8601 string, no spaces, use T)
            place_of_death (Location): place of death of the person a Python Location object

        Returns:
            Person: a Python Person object that wraps the IES Person data
        """

        warnings.warn("IESTool.create_person is deprecated - please initiate Person Python class directly",
                      DeprecationWarning, stacklevel=2)
        kwargs = locals()
        del kwargs['self']
        return self.entity_factory.create_person(**kwargs)

    def create_measure(self, uri: str | None = None, classes: list | None = None,
                       value: str | None = None, uom: UnitOfMeasure | None = None) -> Measure:
        """
        DEPRECATED - Use Measure() to instantiate a measure.

        Args:
            uri (str): the URI of the Measure instance
            classes (list):the IES types to instantiate  - default is Measure
            value (Str): the value of the measure
            uom (UnitOfMeasure): the unit of measure

        Returns:
            Measure - the instance created wrapped as a Python object
        """
        warnings.warn("IESTool.create_measure is deprecated - please initiate Measure Python class directly",
                      DeprecationWarning, stacklevel=2)

        if classes is None:
            classes = [MEASURE]

        return Measure(tool=self, value=value, uom=uom, uri=uri, classes=classes)

    def create_communication(self, uri: str | None = None, classes: list | None = None,
                             starts_in: str | None = None, ends_in: str | None = None,
                             message_content: str | None = None) -> Communication:
        """
        DEPRECATED - Use Communication() to Instantiate an IES Communication class

        Args:
            uri (str): the URI of the Communication instance
            classes (list): the IES types to instantiate  - default is Communication
            starts_in (str): An ISO8601 string (no spaces, use "T" and Zulu only) representing when the
            communication began
            ends_in (str): An ISO8601 string (no spaces, use "T" and Zulu only) representing when the
            communication began
            message_content (str): Optional string showing the content of the communication

        Returns:
            Communication - instance wrapped as a Python Communication object
        """
        logger.warning("IESTool.create_communication deprecated - please initiate Communication Python class directly")

        if classes is None:
            classes = [COMMUNICATION]

        communication = Communication(tool=self, uri=uri, classes=classes, start=starts_in, end=ends_in,
                                      message_content=message_content)
        return communication

    def create_geopoint(
            self, uri: str | None = None, classes: list | None = None,
            lat: float | None = None, lon: float | None = None, precision: int | None = 6
    ) -> GeoPoint:
        """
        DEPRECATED - use GeoPoint() to create an instance of the IES GeoPoint class.

        Args:
            uri (str): the URI of the GeoPoint instance
            classes (list): the IES types to instantiate  - default is GeoPoint
            lat (float): the latitude of the geopoint
            lon (float): the longitude of the geopoint
            precision (int): the precision of the lat lon in decimal places and hence also the produced geohash

        Returns:
            GeoPoint - instance wrapped as a Python GeoPoint object
        """
        warnings.warn("IESTool.create_geopoint is deprecated - please initiate GeoPoint Python class directly",
                      DeprecationWarning,
                      stacklevel=2)

        if classes is None:
            classes = [GEOPOINT]

        for _class in classes:
            if _class not in self.ontology.geopoint_subtypes:
                logger.warning(f"{_class} is not a subtype of ies:GeoPoint")
        return GeoPoint(
            tool=self, uri=uri, lat=lat, lon=lon, precision=precision, classes=classes
        )

    def create_organisation(self, uri: str | None = None, classes: list | None = None,
                            name: str | None = None) -> Organisation:
        """
        DEPRECATED - use Organisation() to create an instance of the IES Organisation class.

        Args:
            uri (str): the URI of the Organisation instance
            classes (list): the IES types to instantiate  - default is Organisation
            name (str): The name of the Organisation

        Returns:
            Organisation:
        """
        warnings.warn("IESTool.create_organisation is deprecated - please initiate Organisation Python class directly",
                      DeprecationWarning, stacklevel=2)

        if classes is None:
            classes = [ORGANISATION]
        return Organisation(
            tool=self, name=name, uri=uri, classes=classes
        )





