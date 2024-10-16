from __future__ import annotations

import io
import json
import logging
import os
import pathlib
import uuid
import warnings
from typing import TypeVar

import iso4217parse
import phonenumbers
import pycountry
import requests
import validators
import validators.uri
from geohash_tools import encode
from pyshacl import validate as pyshacl_validate
from rdflib import XSD, Graph, Literal, Namespace, URIRef

from ies_tool.ies_ontology import IES_BASE, Ontology
from ies_tool.ies_plugin import IESPlugin
from ies_tool.utils import validate_datetime_string

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

IES_TOOL = None

RdfsClassType = TypeVar('RdfsClassType', bound='RdfsClass')

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDFS_RESOURCE = "http://www.w3.org/2000/01/rdf-schema#Resource"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_CLASS = "http://www.w3.org/2000/01/rdf-schema#Class"

TELICENT_PRIMARY_NAME = "http://telicent.io/ontology/primaryName"

EXCHANGED_ITEM = f"{IES_BASE}ExchangedItem"
ELEMENT = f"{IES_BASE}Element"
CLASS_OF_ELEMENT = f"{IES_BASE}ClassOfElement"
CLASS_OF_CLASS_OF_ELEMENT = f"{IES_BASE}ClassOfClassOfElement"
PARTICULAR_PERIOD = f"{IES_BASE}ParticularPeriod"
ACCOUNT = f"{IES_BASE}Account"
ACCOUNT_HOLDER = f"{IES_BASE}AccountHolder"
ACCOUNT_STATE = f"{IES_BASE}AccountState"
AMOUNT_OF_MONEY = f"{IES_BASE}AmountOfMoney"
ASSET = f"{IES_BASE}Asset"
ASSET_STATE = f"{IES_BASE}AssetState"
COMMUNICATIONS_ACCOUNT = f"{IES_BASE}CommunicationsAccount"
COMMUNICATIONS_ACCOUNT_STATE = f"{IES_BASE}CommunicationsAccountState"
HOLDS_ACCOUNT = f"{IES_BASE}holdsAccount"
PROVIDES_ACCOUNT = f"{IES_BASE}providesAccount"
STATE = f"{IES_BASE}State"
BOUNDING_STATE = f"{IES_BASE}BoundingState"
BIRTH_STATE = f"{IES_BASE}BirthState"
DEATH_STATE = f"{IES_BASE}DeathState"
UNIT_OF_MEASURE = f"{IES_BASE}UnitOfMeasure"
MEASURE_VALUE = f"{IES_BASE}MeasureValue"
MEASURE = f"{IES_BASE}Measure"
REPRESENTATION = f"{IES_BASE}Representation"
IDENTIFIER = f"{IES_BASE}Identifier"
NAME = f"{IES_BASE}Name"
NAMING_SCHEME = f"{IES_BASE}NamingScheme"
ENTITY = f"{IES_BASE}Entity"
DEVICE_STATE = f"{IES_BASE}DeviceState"
DEVICE = f"{IES_BASE}Device"
LOCATION = f"{IES_BASE}Location"
LOCATION_STATE = f"{IES_BASE}#LocationState"
COUNTRY = f"{IES_BASE}Country"
GEOPOINT = f"{IES_BASE}GeoPoint"
RESPONSIBLE_ACTOR = f"{IES_BASE}ResponsibleActor"
POST = f"{IES_BASE}Post"
PERSON = f"{IES_BASE}Person"
ORGANISATION = f"{IES_BASE}Organisation"
ORGANISATION_NAME = f"{IES_BASE}OrganisationName"
EVENT = f"{IES_BASE}Event"
EVENT_PARTICIPANT = f"{IES_BASE}EventParticipant"
COMMUNICATION = f"{IES_BASE}Communication"
PARTY_IN_COMMUNICATION = f"{IES_BASE}PartyInCommunication"
WORK_OF_DOCUMENTATION = f"{IES_BASE}WorkOfDocumentation"

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

        # Instances dict is used as a local cache for all instances created. It's a bit wasteful, but it does
        # allow quick access to IES Tool instances
        self.instances: dict = {}

        # Initiate the storage plugins dictionary
        self.plug_in: IESPlugin | None = None

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

    @property
    def default_data_namespace(self):
        return self.prefixes[":"]

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

    def _get_instance(self, uri: str) -> RdfsResource | None:
        """
        Gets an instance (by its URI) that has already been created in this session. Note if you are connected to a
        remote SPARQL server or have loaded data into in-memory graph, pre-existing instances will not have been
        cached by the IESTool.

        Args:
            uri (str): The URI

        Returns:
            RdfsResource: The instance
        """

        if uri in self.instances:
            return self.instances[uri]
        else:
            return None

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
            self.plug_in = plugin
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
    def _str(_input: str | Graph) -> str | Graph:
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
        if self.__mode == "sparql_server":
            logger.warning("Export RDF not supported in sparql server mode")
        elif self.__mode == "plugin":
            if rdf_format not in self.plug_in.supported_rdf_serialisations:
                logger.warning(
                    f"Current plugin only supports {str(self.plug_in.supported_rdf_serialisations)}"
                    f" - you tried to export as {rdf_format}"
                )
            ret_dict["triples"] = self.plug_in.get_rdf()
            ret_dict["warnings"].extend(self.plug_in.get_warnings())
            if clear:
                self.clear_graph()
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
        if classes is None:
            classes = [EVENT]

        return Event(tool=self, start=event_start, end=event_end, uri=uri, classes=classes)

    def create_person(self, uri: str | None = None, classes: list | None = None,
                      given_name: str | None = None, surname: str | None = None, dob: str | None = None,
                      pob: Location | None = None, dod: str | None = None, pod: Location | None = None) -> Person:
        """
        DEPRECATED - use Person() to instantiate an IES Person

        Args:
            given_name (str): first name of the person
            surname (str): surname of the person
            dob (str): date of birth of the person (ISO8601 string, no spaces, use T)
            pob (Location): place of birth of the person a Python Location object
            classes (list): the IES types to instantiate  - default is Person - shouldn't need to change this
            uri (str): the URI of the Person instance - if unset, one will be created.
            dod (str): date of death of the person (ISO8601 string, no spaces, use T)
            pod (Location): place of death of the person a Python Location object

        Returns:
            Person: a Python Person object that wraps the IES Person data
        """

        warnings.warn("IESTool.create_person is deprecated - please initiate Person Python class directly",
                      DeprecationWarning, stacklevel=2)

        if classes is None:
            classes = [PERSON]

        person = Person(
            tool=self, surname=surname, given_name=given_name, start=dob, place_of_birth=pob,
            uri=uri, end=dod, place_of_death=pod, classes=classes
        )

        return person

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


class Unique(type):
    """Metaclass used to manage housekeeping around base class instantiation

    Args:
        type (_type_):
    """

    def __call__(cls, *args, **kwargs):
        if "tool" not in kwargs:
            tool = IES_TOOL
        else:
            tool = kwargs["tool"]
        # Annoyingly, classes doesn't seem to reach this, despite being set as default parameters.
        # classes = kwargs["classes"]
        cache = tool.instances

        if "uri" not in kwargs:
            uri = tool.generate_data_uri()
        else:
            uri = kwargs["uri"]
            if not uri:
                uri = tool.generate_data_uri()
        if not validators.url(uri):
            logger.error(f"Invalid URI: {uri}")
        if uri not in cache:
            self = cls.__new__(cls, args, kwargs)
            cls.__init__(self, *args, **kwargs)
            cache[uri] = self
            return self
        else:
            cached_item = cache[uri]
            return cached_item


class RdfsResource(metaclass=Unique):
    """
    A Python wrapper class for RDFS Resources
    """

    def __init__(
            self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None
    ):
        """
            Instantiate the RDFS Resource

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the RDFS Resource
                classes (list): the RDFS classes to instantiate

            Returns:
                RdfsResource:
        """

        if classes is None or classes == []:
            classes = [RDFS_RESOURCE]
        elif not isinstance(classes, list):
            raise Exception("classes parameter must be a list")
        if tool is None:
            self._tool = IES_TOOL
        else:
            self._tool = tool
        if not uri:
            self._uri = self.tool.generate_data_uri()
        else:
            self._uri = uri

        for cls in classes:
            self.tool.add_triple(subject=self._uri, predicate=RDF_TYPE, obj=cls)
        self._classes = classes

        self.tool.instances[self._uri] = self

    @property
    def tool(self):
        return self._tool

    @property
    def uri(self):
        return self._uri

    @property
    def labels(self):
        return self.tool.make_results_list_from_query(
            "SELECT ?l WHERE {<" + self._uri + "> <http://www.w3.org/2000/01/rdf-schema#label> ?l }", "l")

    @property
    def comments(self):
        return self.tool.make_results_list_from_query(
            "SELECT ?c WHERE {<" + self._uri + "> <http://www.w3.org/2000/01/rdf-schema#comment> ?c }", "c")

    def add_type(self, class_uri) -> None:
        """Adds a rdf:type predicate from this object to a rdfs:Class referenced by the class_uri

        Args:
            class_uri (_type_): the rdfs:Class to reference
        """
        self.tool.add_triple(self.uri, predicate=RDF_TYPE, obj=class_uri)

    def add_literal(self, predicate: str, literal: str, literal_type: str = "string") -> None:
        """Adds a triple where the object is a literal

        Args:
            predicate (str): the uri of the predicate (as a fully formed URI)
            literal (str): the literal string to be assigned
            literal_type (str, optional): a valid xsd datatype without the prefix. Defaults to "string".

        Returns:
            _type_: _description_
        """
        self.tool.add_triple(self._uri, predicate, literal, is_literal=True, literal_type=literal_type)

    def add_label(self, label: str):
        """Adds a rdfs label to the node

        Args:
            label (str): The text string of the label
        """
        self.add_literal(predicate=self.tool.rdfs_label, literal=label)

    def add_comment(self, comment: str):
        """Adds a rdfs comment to this node

        Args:
            comment (str): The text string of the comment
        """
        self.add_literal(predicate=self.tool.rdfs_comment, literal=comment)

    def add_telicent_primary_name(self, name: str):
        """Adds a telicent primary name to the node - for use in the Telicent CORE platform

        Args:
            name (_type_): The text string of the name
        """
        self.add_literal(predicate=TELICENT_PRIMARY_NAME, literal=name)

    def add_related_object(self, predicate: str, related_object) -> bool:
        """Adds a predicate to relate this node to another via a specified predicate

        Args:
            predicate (str): the URI of the rdf property of the predicate
            related_object (): Either an object (subtype of RdfsResource) or a string representing the URI of the object

        Returns:
            bool:
        """
        related_object = self._validate_referenced_object(related_object, context="add_relation")
        return self.tool.add_triple(self._uri, predicate=predicate, obj=related_object, is_literal=False)

    def _validate_referenced_object(self, reference, base_type: Unique | None = None,
                                    context: str | None = None) -> RdfsResource:
        """
        An internal method for ascertaining the best base class of a given URI.
        If you pass it an object, it just returns the object you gave it

        Args:
            reference (): Either an object (subtype of RdfsResource) or a URI referance to an instance (i.e. a string)
            base_type (Unique, optional): Used to override the type of object return if one is being inferred
                (i.e. when a string is passed). Defaults to None.
            context (str, optional): A helper string for debugging output. Defaults to "".

        Raises:
            Exception: An exception is raised if something that is neither a string or a base class is passed

        Returns:
            RdfsResource: The provided or inferred object
        """
        if context is None:
            context = ""

        if isinstance(reference, str):
            inst = self.tool._get_instance(reference)
            if inst is not None:
                return inst
            else:
                logger.warning(
                    f'''String passed instead of object in {context}
                    - assumed URI is defined elsewhere: {reference}
                    - base class {base_type.__name__} has been inferred'''
                )
                if base_type is None:
                    base_type = RdfsResource
                return base_type(tool=self.tool, uri=reference, classes=[])
        elif isinstance(reference, RdfsResource):
            return reference
        else:
            raise Exception(f"Unknown type {str(type(reference))} in {context}")


class RdfsClass(RdfsResource):
    """
        A Python wrapper class for RDFS Class
    """

    def __init__(
            self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None
    ):
        """
            Instantiate the RDFS Class

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the RDFS Class
                classes (list): the IES types to instantiate (default is rdfs:Class)

            Returns:
                RdfsClass:
        """
        if classes is None:
            classes = [RDFS_CLASS]
        super().__init__(tool=tool, uri=uri, classes=classes)

    def instantiate(self, uri=None) -> RdfsResource:
        """Creates an instance of this class

        Args:
            uri (_type_, optional): _description_. Defaults to None.

            Returns:
                RdfsResource:
        """
        return self.tool.instantiate([self.uri], uri, base_class=self)

    def add_sub_class(self, sub_class: str) -> bool:
        """adds a subClassOf relationship to the provided sub_class

        Args:
            sub_class (str): the uri of the class that will inherit from this one in the RDF

        Returns:
            bool:
        """
        return self.tool.add_triple(sub_class, f"{RDFS}subClassOf", self.uri)


class ExchangedItem(RdfsResource):
    """
        A Python wrapper class for IES ExchangedItem
    """

    def __init__(
            self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES ExchangedItem

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES ExchangedItem
                classes (list): the IES types to instantiate

            Returns:
                ExchangedItem:
        """
        if classes is None:
            classes = [EXCHANGED_ITEM]
        super().__init__(tool=tool, uri=uri, classes=classes)

    def add_representation(
            self, representation_text: str, representation_class: str | None = REPRESENTATION,
            uri: str | None = None, rep_rel_type: str | None = None, naming_scheme=None) -> Representation:
        """Adds a new IES representation to this node

        Args:
            representation_text (str):
            representation_class (str | None, optional): the URI. Defaults to ies:Representation".
            uri (str | None, optional): _description_. Defaults to None.
            rep_rel_type (str | None, optional): _description_. Defaults to None.
            naming_scheme (_type_, optional): _description_. Defaults to None.

        Returns:
            Representation: _description_
        """
        if not rep_rel_type:
            rep_rel_type = f"{IES_BASE}isRepresentedAs"
        representation = Representation(
            tool=self.tool, representation_text=representation_text, uri=uri,
            classes=[representation_class], naming_scheme=naming_scheme
        )
        self.tool.add_triple(subject=self._uri, predicate=rep_rel_type, obj=representation._uri)
        return representation

    def add_name(
            self, name, name_class: str | None = None, uri=None, name_rel_type=None,
            naming_scheme=None) -> Name:
        """
        Adds an IES name to the node

        Args:
            name (_type_): The text of the name
            name_class (str | None, optional): The subclass of ies:Name to use if needed. Defaults to IES Name".
            uri (_type_, optional): set uri to override generated URI for the ies:Name object. Defaults to None.
            name_rel_type (_type_, optional): used to override the naming relationship. Defaults to None.
            naming_scheme (_type_, optional): connect the ies:Name instance to a NamingScheme. Defaults to None.

        Returns:
            Name:
        """
        if name_rel_type is None:
            name_rel_type = f"{IES_BASE}hasName"

        if name_class is None:
            name_class = NAME

        representation = Name(
            tool=self.tool, name_text=name, uri=uri,
            classes=[name_class], naming_scheme=naming_scheme
        )
        self.tool.add_triple(subject=self._uri, predicate=name_rel_type, obj=representation._uri)
        return representation

    def add_identifier(
            self, identifier, id_class: str | None = None, uri=None, id_rel_type=None,
            naming_scheme=None) -> Identifier:
        """
        Adds an IES identifier to the node

        Args:
            identifier (_type_): the text of the identifier
            id_class (str | None, optional): The subclass of ies:Identifier to use if needed.
                Defaults to IES Identifier".
            uri (_type_, optional): set uri to override generated URI for the ies:Identifier object. Defaults to None.
            id_rel_type (_type_, optional): used to override the identification relationship. Defaults to None.
            naming_scheme (_type_, optional): connect the ies:Identifier instance to a NamingScheme. Defaults to None.

        Returns:
            Identifier:
        """
        if id_rel_type is None:
            id_rel_type = f"{IES_BASE}isIdentifiedBy"

        if id_class is None:
            id_class = IDENTIFIER

        representation = Identifier(
            tool=self.tool, id_text=identifier, uri=uri, classes=[id_class], naming_scheme=naming_scheme
        )
        self.tool.add_triple(subject=self._uri, predicate=id_rel_type, obj=representation._uri)
        return representation


class Element(ExchangedItem):
    """
        A Python wrapper class for IES Element
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Element

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Element
                classes (list): the IES types to instantiate (default is ies:Element)
                start (str): an ISO8601 datetime string that marks the start of the Element
                end (str): an ISO8601 datetime string that marks the end of the Element
            Returns:
                Element:
        """
        if classes is None:
            classes = [ELEMENT]

        super().__init__(tool=tool, uri=uri, classes=classes)
        self._default_state_type = STATE

        if start:
            self.starts_in(start)
        if end:
            self.ends_in(end)

    def add_part(self, part: Element | str, part_rel_type: str = None):
        """_summary_

        Args:
            part (Element | str): _description_
            part_rel_type (str, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        part_object = self._validate_referenced_object(part, Element, "add_part")
        if part_rel_type is None:
            part_rel_type = f"{IES_BASE}isPartOf"
        self.tool.add_triple(part_object.uri, part_rel_type, self._uri)
        return part_object

    def create_state(
            self, state_type: str | None = None, uri: str | None = None,
            state_rel: str | None = None, start: str | None = None, end: str | None = None,
            in_location: Location | None = None
    ) -> State:
        """Creates a state of this node

        Args:
            state_type (str | None, optional): The type of state - must be subclass of ies:State. Defaults to None.
            uri (str | None, optional): Use to override the uri of the state. Defaults to ies:State.
            state_rel (str | None, optional): use to override the state relationship . Defaults to ies:isStateOf.
            start (str | None, optional): an iso8601 string representing the start of the State. Defaults to None.
            end (str | None, optional): an iso8601 string representing the end of the State. Defaults to None.
            in_location (Location | None, optional): Add a location for the state. Defaults to None.

        Returns:
            State:
        """

        if not state_type:
            state_type = self._default_state_type

        state = State(tool=self.tool, start=start, end=end, uri=uri, classes=[state_type])

        if not state_rel:
            state_rel = f"{IES_BASE}isStateOf"

        self.tool.add_triple(subject=state._uri, predicate=state_rel, obj=self._uri)

        if in_location is not None:
            state.in_location(in_location)
        return state

    def add_state(
            self, state_type: str | None = None, uri: str | None = None,
            state_rel: str | None = None, start: str | None = None, end: str | None = None,
            in_location: Location | None = None
    ) -> State:
        """
        DEPRECATED - use create_state()
        """
        logger.warning("add_state() is deprecated - use create_state()")
        return self.create_state(state_type=state_type, uri=uri, state_rel=state_rel,
                                 start=start, end=end, in_location=in_location)

    def in_location(self, location: Location | str) -> Location:
        """Places the Element in a Location

        Args:
            location (Location | str): A location object or uri string of a location object

        Returns:
            Location:
        """
        location_object = self._validate_referenced_object(location, Location, "in_location")
        self.tool.add_triple(
            subject=self.uri, predicate=f"{IES_BASE}inLocation",
            obj=location_object.uri)
        return location_object

    @validate_datetime_string
    def put_in_period(self, time_string: str) -> ParticularPeriod:
        """
        Puts an item in a particular period

        Args:
            time_string (str): An ISO8601 datetime string

        Returns:
            ParticularPeriod:
        """
        pp_instance = ParticularPeriod(tool=self.tool, time_string=time_string)
        self.tool.add_triple(self._uri, f"{IES_BASE}inPeriod", pp_instance._uri)
        return pp_instance

    @validate_datetime_string
    def starts_in(self, time_string: str, bounding_state_class: str | None = None,
                  uri: str | None = None) -> BoundingState:
        """
        Asserts an item started in a particular period

        Args:
            time_string (str): An ISO8601 datetime string representing the start period
            bounding_state_class (str | None, optional): Used to override the type of bounding state. Defaults to None.
            uri (str | None, optional): Used to override the URI of the produced state. Defaults to None.

        Returns:
            BoundingState:
        """

        if bounding_state_class is None:
            bounding_state_class = f"{IES_BASE}BoundingState"

        bs = BoundingState(tool=self.tool, classes=[bounding_state_class], uri=uri)
        self.tool.add_triple(subject=bs._uri, predicate=f"{IES_BASE}isStartOf",
                             obj=self._uri)
        if time_string:
            bs.put_in_period(time_string=time_string)
        return bs

    @validate_datetime_string
    def ends_in(self, time_string: str, bounding_state_class: str | None = None,
                uri: str | None = None) -> BoundingState:
        """Asserts an item ended in a particular period.

        Args:
            time_string (str): An ISO8601 datetime string representing the end period
            bounding_state_class (str | None, optional): Used to override the type of bounding state. Defaults to None.
            uri (str | None, optional): Used to override the URI of the produced state. Defaults to None.

        Returns:
            BoundingState: _description_
        """
        if bounding_state_class is None:
            bounding_state_class = BOUNDING_STATE

        bs = BoundingState(tool=self.tool, classes=[bounding_state_class], uri=uri)
        self.tool.add_triple(subject=bs._uri, predicate=f"{IES_BASE}isEndOf",
                             obj=self._uri)
        if time_string:
            bs.put_in_period(time_string=time_string)
        return bs

    def add_measure(self, value, measure_class=None, uom=None, uri: str = None):
        """
        Creates a new Measure and applies it to the node

        Args:
            value (_type_): the value of the measure
            measure_class (_type_, optional): _description_. Defaults to ies:MeasureClass.
            uom (_type_, optional): the unit of measure. Defaults to None.
            uri (str, optional): used to override the measure uri. Defaults to None.
        """
        measure = Measure(
            tool=self.tool, uri=uri, classes=[measure_class], value=value, uom=uom
        )
        self.tool.add_triple(
            subject=self._uri, predicate=f"{IES_BASE}hasCharacteristic", obj=measure._uri
        )


class Entity(Element):
    """
        A Python wrapper class for IES Entity
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Entity

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Entity
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Entity
                end (str): an ISO8601 datetime string that marks the end of the Entity
            Returns:
                Entity:
        """
        if classes is None:
            classes = [ENTITY]
        super().__init__(
            tool=tool, uri=uri, classes=classes, start=start, end=end
        )


class State(Element):
    """
        A Python wrapper class for IES State
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES State

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES State
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the State
                end (str): an ISO8601 datetime string that marks the end of the State
            Returns:
                State:
        """
        if classes is None:
            classes = [STATE]
        super().__init__(
            tool=tool, uri=uri, classes=classes, start=start, end=end
        )


class DeviceState(State):
    """
        A Python wrapper class for IES DeviceState
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES DeviceState

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES DeviceState
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the DeviceState
                end (str): an ISO8601 datetime string that marks the end of the DeviceState

            Returns:
                DeviceState:
        """
        if classes is None:
            classes = [DEVICE_STATE]
        super().__init__(
            tool=tool, uri=uri, classes=classes, start=start, end=end
        )

    def add_imsi(self, imsi: str) -> Identifier:
        """
        Creates an IMSI identifier for the Device or DeviceState

        Args:
            imsi (str): a valid IMSI code
        Returns:
            Identifier:
        """
        if not len(imsi.replace("IMSI", "")) not in (14, 15):
            logger.warning(f"IMSI: {imsi} does not appear to be valid")
        uri = f"{self.tool.prefixes['IMSI:']}{imsi.replace(' ', '').replace('IMSI:', '')}"
        return self.add_identifier(imsi, id_class=f'{IES_BASE}IMSI', uri=uri)

    def add_mac_address(self, mac_address: str) -> Identifier:
        """
        Creates a MAC identifier for the Device or DeviceState

        Args:
            mac_address (str): A valid MAC ID
        Returns:
            Identifier:
        """
        if not validators.mac_address(mac_address):
            logger.warning(f"MAC address {mac_address} does not appear to be valid")
        uri = self.tool.prefixes["ieee802:"] + mac_address.replace(" ", "").replace(":", "")
        return self.add_identifier(mac_address, id_class=f'{IES_BASE}MACAddress', uri=uri)

    def add_ip_address(self, ip_address: str) -> Identifier:
        """
        Creates an IP Address for the Device or DeviceState

        Args:
            ip_address (str): a valid IPv4 or IPv6 IP Address

        Returns:
            Identifier:
        """
        if validators.ipv4(ip_address):
            cls = f"{IES_BASE}IPv4Address"
        elif validators.ipv6(ip_address):
            cls = f"{IES_BASE}IPv6Address"
        else:
            cls = f"{IES_BASE}IPAddress"
        return self.add_identifier(ip_address, id_class=cls)

    def add_callsign(self, callsign: str) -> Identifier:
        """
        Creates a Callsign for the Device or DeviceState

        Args:
            callsign (str): the callsign text

        Returns:
            Identifier:
        """
        return self.add_identifier(callsign, id_class=f'{IES_BASE}Callsign')


class Asset(Entity):
    """
        A Python wrapper class for IES Asset
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Device

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Asset
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Asset
                end (str): an ISO8601 datetime string that marks the end of the Asset

            Returns:
                Device:
        """
        if classes is None:
            classes = [ASSET]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = ASSET_STATE


class AmountOfMoney(Asset):
    """
        A Python wrapper class for IES AmountOfMoney
    """

    def __init__(self, /, tool: IESTool = IES_TOOL, *, amount: float, iso_4217_currency_code_alpha3: str,
                 uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES AmountOfMoney

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Device
                classes (list): the IES types to instantiate

            Returns:
                AmountOfMoney:
        """
        if classes is None:
            classes = [AMOUNT_OF_MONEY]

        super().__init__(tool=tool, uri=uri, classes=classes)

        currency = iso4217parse.by_alpha3(iso_4217_currency_code_alpha3)
        if currency is None:
            logger.error(f"Unrecognised ISO4217 alpha3 currency code {iso_4217_currency_code_alpha3}")

        currency_uri = self.tool.prefixes["iso4217:"] + iso_4217_currency_code_alpha3

        currency_object = self.tool._get_instance(currency_uri)
        if currency_object is None:
            currency_object = ClassOfElement(tool=self.tool, uri=currency_uri, classes=[IES_BASE + "Currency"])
            currency_object.add_identifier(iso_4217_currency_code_alpha3)
            if currency:
                currency_object.add_name(currency.name)

        self.tool.add_triple(self.uri, f"{IES_BASE}currencyDenomination", currency_uri)
        self.tool.add_triple(self.uri, f"{IES_BASE}currencyAmount", str(amount),
                             is_literal=True, literal_type="decimal")

        self._default_state_type = ASSET_STATE


class Device(Asset, DeviceState):
    """
        A Python wrapper class for IES Device
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Device

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Device
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Device
                end (str): an ISO8601 datetime string that marks the end of the Device

            Returns:
                Device:
        """
        if classes is None:
            classes = [DEVICE]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = DEVICE_STATE


class Account(Entity):
    """
        A Python wrapper class for IES Account
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate an IES Account

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Account instance
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Account
                end (str): an ISO8601 datetime string that marks the end of the Account

            Returns:
                Account:
        """
        if classes is None:
            classes = [ACCOUNT]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = ACCOUNT_STATE

    def add_account_number(self, account_number: str) -> Identifier:
        """
        Creates an account number identifier for the Account

        Args:
            account_number (str): the account number

        Returns:
            Identifier:
        """
        id_uri_acc_no = self.tool._mint_dependent_uri(self.uri, "ACC_NO")
        return self.add_identifier(identifier=account_number, uri=id_uri_acc_no, id_class=f"{IES_BASE}AccountNumber")

    def add_account_holder(self, holder, start: str | None = None, end: str | None = None,
                           state_uri: str | None = None) -> State:
        """
            add an AccountHolder to the Account

            Args:
                holder: an instance of a ReponsibleActor (or subclass) or a URI string (not recommended)
                start (str): an ISO8601 datetime string that marks the start of the AccountHolder state
                end (str): an ISO8601 datetime string that marks the end of the AccountHolder state
                state_uri (str): used to override the URI of the created state (optional)

            Returns:
                State:
        """
        holder_object = self._validate_referenced_object(holder, ResponsibleActor, "add_account_holder")
        holder_state = holder_object.create_state(state_type=ACCOUNT_HOLDER, uri=state_uri, start=start, end=end)
        self.tool.add_triple(holder_state.uri, HOLDS_ACCOUNT, self.uri)
        return holder_state

    def add_account_provider(self, provider) -> bool:
        """
            link the Account to its provider

            Args:
                provider: an instance of a ReponsibleActor (or subclass) or a URI string (not recommended)

            Returns:
                bool:
        """
        provider_object = self._validate_referenced_object(provider, ResponsibleActor, "add_account_provider")
        return self.tool.add_triple(provider_object.uri, PROVIDES_ACCOUNT, self.uri)

    def add_registered_telephone_number(self, telephone_number: str, start: str | None = None,
                                        end: str | None = None) -> Identifier:
        """
        Adds the registered telephone number for the account

        Args:
            telephone_number (str): A valid telephone number with country code
            start (str | None, optional): the start date fron which this was registered. Defaults to None.
            end (str | None, optional): the date when the number was de-registered. Defaults to None.

        Returns:
            Identifier:
        """
        try:
            tel = phonenumbers.parse(telephone_number, None)
            normalised = phonenumbers.format_number(tel, phonenumbers.PhoneNumberFormat.E164)
            ph_uri = self.tool.prefixes["e164:"] + normalised.replace("+", "")
        except Exception as e:
            logger.warning(f"telephone number: {telephone_number} could not be parsed {str(e)}")
            normalised = telephone_number
            ph_uri = None
        state_uri = self.tool._mint_dependent_uri(self.uri, "REG_PHONE")
        state = self.create_state(uri=state_uri, start=start, end=end)
        tel_no = Identifier(self.tool, id_text=normalised, uri=ph_uri, classes=[f"{IES_BASE}TelephoneNumber"])
        self.tool.add_triple(subject=state.uri, predicate=f"{IES_BASE}hasRegisteredCommsID", obj=tel_no.uri)
        return tel_no

    def add_registered_email_address(self, email_address: str, start: str | None = None,
                                     end: str | None = None) -> Identifier:
        """
        Adds the registered email address for the account

        Args:
            email_address (str): A valid e-mail address
            start (str | None, optional): the start date fron which this was registered. Defaults to None.
            end (str | None, optional):the date when the email address was de-registered. Defaults to None.

        Returns:
            Identifier:
        """
        if validators.email(email_address):
            em_uri = self.tool.prefixes["rfc5322:"] + email_address
        else:
            logger.warning(f"email address: {email_address} could not be validated")
            em_uri = None

        state_uri = self.tool._mint_dependent_uri(self.uri, "REG_EMAIL")
        state = self.create_state(uri=state_uri, start=start, end=end)
        email_obj = Identifier(self.tool, id_text=email_address, uri=em_uri, classes=[f"{IES_BASE}EmailAddress"])
        self.tool.add_triple(subject=state.uri, predicate=f"{IES_BASE}hasRegisteredCommsID", obj=email_obj.uri)
        return email_obj


class CommunicationsAccount(Account):
    """
        A Python wrapper class for IES Account
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate an IES CommunicationsAccount

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES CommunicationsAccount
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the CommunicationsAccount
                end (str): an ISO8601 datetime string that marks the end of the CommunicationsAccount

            Returns:
                CommunicationsAccount:
        """
        if classes is None:
            classes = [COMMUNICATIONS_ACCOUNT]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = COMMUNICATIONS_ACCOUNT_STATE


class Location(Entity):
    """
        A Python wrapper class for IES Location
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Location

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Location
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Location
                end (str): an ISO8601 datetime string that marks the end of the Location

            Returns:
                Location:
        """
        if classes is None:
            classes = [LOCATION]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = LOCATION_STATE


class Country(Location):
    """
    Python wrapper class for IES Country, where ISO country code forms the URI
    """

    def __init__(self, /,tool: IESTool = IES_TOOL, *,country_alpha_3_code: str, country_name: str = None,
                 classes: list[str] | None = None, uri: str = None, validate: bool = True):
        """
            Instantiate the IES Country

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                country_alpha_3_code: ISO3166 alpha3 code
            Returns:
                Country:
        """

        uri = f"http://iso.org/iso3166#{country_alpha_3_code}"

        if not classes:
            classes = [COUNTRY]

        super().__init__(tool=tool, uri=uri, classes=classes)

        if validate:
            try:
                pycountry_obj = pycountry.countries.get(alpha_3=country_alpha_3_code)
                if pycountry_obj is None:
                    logger.error(f"country code: {country_alpha_3_code} could not be validated")
                if country_name:
                    if country_name != pycountry_obj.name:
                        logger.warning(f"Country name '{country_name}' doesn't match '{pycountry_obj.name}'")
                        self.add_country_name(pycountry_obj.name)
                else:
                    country_name = pycountry_obj.name
            except Exception as e:
                logger.error(f"country code: {country_alpha_3_code} could not be validated {str(e)}")

        self.add_identifier(country_alpha_3_code, id_class=IES_BASE + "ISO3166_1Alpha_3", uri=uri + "_ISO3166_1Alpha_3")
        if country_name:
            self.add_country_name(country_name)

    def add_country_name(self, name: str) -> Name:
        """
        Adds a Placename for the Country

        Args:
            name (str): the country's name

        Returns:
            Name:
        """
        name_uri = self.tool._mint_dependent_uri(self.uri, "NAME")
        return self.add_name(name, name_class=IES_BASE + "PlaceName", uri=name_uri)


class GeoPoint(Location):
    """
    Python wrapper class for IES GeoPoint, with geo-hashes used to make the URI
    """

    def __init__(self, tool: IESTool = IES_TOOL, classes: list[str] | None = None,
                 lat: float = None, lon: float = None, precision: int = None):
        """
            Instantiate the IES GeoPoint

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                classes (list): the IES types to instantiate
                lat (float): the latitude of the GeoPoint as a decimal
                lon (float): the longitude of the GeoPOint as a decimal
                precision (int): number of decimal places for lat and lon
                start (str): an ISO8601 datetime string that marks the start of the GeoPoint
                end (str): an ISO8601 datetime string that marks the end of the GeoPoint
            Returns:
                GeoPoint:
        """
        if classes is None:
            classes = [GEOPOINT]

        uri = "http://geohash.org/" + str(encode(float(lat), float(lon), precision=precision))
        super().__init__(tool=tool, uri=uri, classes=classes)

        lat_uri = f"{uri}_LAT"
        lon_uri = f"{uri}_LON"

        self.add_identifier(identifier=str(lat), uri=lat_uri,
                            id_class=f"{IES_BASE}Latitude")

        self.add_identifier(identifier=str(lon), uri=lon_uri,
                            id_class=f"{IES_BASE}Longitude")


class ResponsibleActor(Entity):
    """
    Python wrapper class for IES ResponsibleActor
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES ResponsibleActor

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES ResponsibleActor
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the ResponsibleActor
                end (str): an ISO8601 datetime string that marks the end of the ResponsibleActor

            Returns:
                ResponsibleActor:
        """
        if classes is None:
            classes = [RESPONSIBLE_ACTOR]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = f"{IES_BASE}ResponsibleActorState"

    def works_for(self, employer: ResponsibleActor | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the responsible actor works for another responsible actor

        Args:
            employer (ResponsibleActor | str): The ReponsibleActor that is the employer (or uri referring to)
            start (str | None, optional): an ISO8601 datetime string - the start of the employment. Defaults to None.
            end (str | None, optional): an ISO8601 datetime string - the end of the employment. Defaults to None.

        Returns:
            State:
        """
        employer_object = self._validate_referenced_object(employer, ResponsibleActor, "works_for")
        state = self.create_state(start=start, end=end)
        self.tool.add_triple(subject=state._uri, predicate=f"{IES_BASE}worksFor",
                             obj=employer_object._uri)
        return state

    def in_post(self, post: Post | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the ReponsibleActor is in a Post

        Args:
            post (Post | str): The post they are in
            start (str | None, optional): an ISO8601 datetime string - the start of in-post. Defaults to None.
            end (str | None, optional): an ISO8601 datetime string - the end of in-post. Defaults to None.

        Returns:
            Post:
        """
        post_object = self._validate_referenced_object(post, Post, "in_post")
        in_post = self.create_state(state_type=f"{IES_BASE}InPost", start=start, end=end)
        post_object.add_part(in_post)
        return in_post

    def has_access_to(self, accessed_item: Entity | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the ResponsibleActor has access to an Entity

        Args:
            accessed_item (Entity | str): The Entity (or reference to) that is accessed
            start (str | None, optional): The start of the access period - ISO8601 string. Defaults to None.
            end (str | None, optional): The end of the access period - ISO8601 string. Defaults to None.

        Returns:
            State:
        """
        accessed_object = self._validate_referenced_object(accessed_item, Entity, "has_access_to")
        access = self.create_state(start=start, end=end)
        self.tool.add_triple(access.uri, f"{IES_BASE}hasAccessTo", accessed_object.uri)
        return access

    def in_possession_of(self, accessed_item: Entity | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the ResponsibleActor has possession of an Entity (not legal ownership)

        Args:
            accessed_item (Entity | str): The Entity (or reference to) that is possessed
            start (str | None, optional): The start of the possession period - ISO8601 string. Defaults to None.
            end (str | None, optional): The end of the possession period - ISO8601 string. Defaults to None.

        Returns:
            State: _description_
        """
        accessed_object = self._validate_referenced_object(accessed_item, Entity, "in_possession_of")
        access = self.create_state(start=start, end=end)
        self.tool.add_triple(access.uri, f"{IES_BASE}inPossessionOf", accessed_object.uri)
        return access

    def user_of(self, accessed_item: Entity | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the ResponsibleActor has use of an Entity (not legal ownership)

        Args:
            accessed_item (Entity | str): The Entity (or reference to) that is in use
            start (str | None, optional): The start of the usage period - ISO8601 string. Defaults to None.
            end (str | None, optional): The end of the usage period - ISO8601 string. Defaults to None.

        Returns:
            State:
        """
        accessed_object = self._validate_referenced_object(accessed_item, Entity, "user_of")
        access = self.create_state(start=start, end=end)
        self.tool.add_triple(access.uri, f"{IES_BASE}userOf", accessed_object.uri)
        return access

    def owns(self, owned_item: Entity | str, start: str | None = None, end: str | None = None) -> State:
        """
        Asserts the ResponsibleActor has legal ownership of an Entity

        Args:
            owned_item (Entity | str): the Entity that is owned
            start (str | None, optional): The start of the ownership period - ISO8601 string. Defaults to None.
            end (str | None, optional): The end of the ownership period - ISO8601 string. Defaults to None.

        Returns:
            State:
        """
        owned_object = self._validate_referenced_object(owned_item, Asset, "owns")
        owned = self.create_state(start=start, end=end)
        self.tool.add_triple(owned.uri, f"{IES_BASE}owns", owned_object.uri)
        return owned


class Post(ResponsibleActor):
    """
    Python wrapper class for IES Post
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Post

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Post
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Post
                end (str): an ISO8601 datetime string that marks the end of the Post

            Returns:
                Post:
        """
        if classes is None:
            classes = [POST]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        if start is not None:
            self.starts_in(start)
        if end is not None:
            self.ends_in(end)


class Person(ResponsibleActor):
    """
    Python wrapper class for IES Person
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None, surname: str | None = None,
                 given_name: str | None = None, date_of_birth: str | None = None, date_of_death: str | None = None,
                 place_of_birth: Location | None = None, place_of_death: Location | None = None,
                 family_name: str | None = None):
        """
            Instantiate an IES Person Class

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Person
                classes (list): the IES types to instantiate (default is ies:Person)
                start (str): an ISO8601 datetime string that marks the birth of the Person
                end (str): an ISO8601 datetime string that marks the death of the Person
                surname (str): surname of the person
                given_name (str): the first name of the Person
                date_of_birth (str): an ISO8601 datetime string that marks the birth - use in preference to start
                date_of_death (str): an ISO8601 datetime string that marks the death - use in preference to end
                place_of_birth (Location): the place of birth of the Person
                place_of_dearh (Location): the place of death of the Person
            Returns:
                Person:
        """
        if classes is None:
            classes = [PERSON]

        super().__init__(tool=tool, uri=uri, classes=classes, start=None, end=None)

        if date_of_birth is not None:
            if start is not None:
                raise Exception("start and date_of_birth cannot both be set for Person")
            start = date_of_birth

        if date_of_death is not None:
            if end is not None:
                raise Exception("end and date_of_death cannot both be set for Person")
            end = date_of_death

        self._default_state_type = f"{IES_BASE}PersonState"

        if given_name:
            self.add_given_name(given_name=given_name)

        if surname:
            self.add_surname(surname=surname)
            if family_name:
                logger.error("family_name parameter is deprecated equivalent of surname - do not set both")
        else:
            if family_name:
                self.add_surname(surname=surname)
                logger.warning("family_name parameter is deprecated - please use surname")

        if start is not None:
            self.add_birth(start, place_of_birth)

        if end is not None:
            self.add_death(end, place_of_death)

    def add_given_name(self, given_name: str) -> Name:
        """
        Adds a GivenName to a Person

        Args:
            given_name (str): the given name of the person

        Returns:
            Name:
        """
        name_uri_firstname = self.tool._mint_dependent_uri(self.uri, "GIVENNAME")
        return self.add_name(given_name, uri=name_uri_firstname,
                             name_class=f"{IES_BASE}GivenName")

    def add_surname(self, surname: str) -> Name:
        """
        Adds a Surname to a Person

        Args:
            surname (str): the person's surname

        Returns:
            Name:
        """
        name_uri_surname = self.tool._mint_dependent_uri(self.uri, "SURNAME")
        return self.add_name(surname, uri=name_uri_surname,
                             name_class=f"{IES_BASE}Surname")

    def add_birth(self, date_of_birth: str, place_of_birth: Location | str = None) -> BoundingState:
        """
        Adds birth state to a Person

        Args:
            date_of_birth (str): Date of birth represented as an ISO8601 string
            place_of_birth (Location | str, optional): The Location of birth (or URI reference to it). Defaults to None.

        Returns:
            BoundingState:
        """
        birth_uri = self.tool._mint_dependent_uri(self.uri, "BIRTH")
        birth = self.starts_in(time_string=date_of_birth, bounding_state_class=f"{IES_BASE}BirthState",
                               uri=birth_uri)
        if place_of_birth:
            pob_object = self._validate_referenced_object(place_of_birth, Location, "add_birth")
            self.tool.add_triple(birth._uri, f"{IES_BASE}inLocation", pob_object._uri)
        return birth

    def add_death(self, date_of_death: str, place_of_death: Location | str = None) -> BoundingState:
        """
        Adds death state to a Person

        Args:
            date_of_death (str): Date of death represented as an ISO8601 string
            place_of_death (Location | str, optional): The Location of death (or URI reference to it). Defaults to None.

        Returns:
            BoundingState:
        """

        uri = self.tool._mint_dependent_uri(self.uri, "DEATH")
        death = self.ends_in(
            date_of_death, bounding_state_class=f"{IES_BASE}DeathState", uri=uri
        )
        if place_of_death:
            pod_object = self._validate_referenced_object(place_of_death, Location, "add_death")
            self.tool.add_triple(death._uri, f"{IES_BASE}inLocation", pod_object._uri)

        return death


class Organisation(ResponsibleActor):
    """
    Python wrapper class for IES Organisation
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list | None = None,
                 start: str | None = None, end: str | None = None, name=None):
        """
            Instantiate the IES Organisation

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Organisation
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Organisation
                end (str): an ISO8601 datetime string that marks the end of the Organisation

            Returns:
                Organisation:
        """
        if classes is None:
            classes = [ORGANISATION]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self._default_state_type = f"{IES_BASE}OrganisationState"

        if name:
            self.add_name(name, name_class=ORGANISATION_NAME)

    def create_post(self, name: str, start: str | None = None, end: str | None = None, uri: str | None = None) -> Post:
        """
        Creates a new post in the organisation

        Args:
            name (str): the name of the post
            start (str | None, optional): An ISO8601 string marking start of post. Defaults to None.
            end (str | None, optional): An ISO8601 string marking end of post. Defaults to None.
            uri (str | None, optional): Use to override post URI. Defaults to None.

        Returns:
            Post: _description_
        """
        if uri is None:
            uri = self.tool._mint_dependent_uri(self.uri, "POST")
        post = Post(tool=self.tool, uri=uri, start=start, end=end)
        if name is not None and name != "":
            post.add_name(name)
        self.add_part(post)
        return post


class ClassOfElement(RdfsClass, ExchangedItem):
    """
    Python wrapper class for IES ClassOfElement
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES ClassOfElement

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES ClassOfElement
                classes (list): the IES types to instantiate

            Returns:
                ClassOfElement:
        """
        if classes is None:
            classes = [CLASS_OF_ELEMENT]
        super().__init__(tool=tool, uri=uri, classes=classes)

    def add_measure(self, value: str, measure_class: str | None = None,
                    uom: UnitOfMeasure | None = None, uri: str = None):
        """
        Creates a new Measure and applies it to the class - meaning all members possess this measure

        Args:
            value (str): the value of the measure
            measure_class (str, optional): _description_. Defaults to ies:MeasureClass.
            uom (UnitOfMeasure, optional): the unit of measure. Defaults to None.
            uri (str, optional): used to override the measure uri. Defaults to None.
        """
        measure = Measure(
            tool=self.tool, value=value, uom=uom, uri=uri, classes=[measure_class]
        )
        self.tool.add_triple(subject=self._uri,
                             predicate=f"{IES_BASE}allHaveCharacteristic",
                             obj=measure._uri)


class ClassOfClassOfElement(RdfsClass, ExchangedItem):
    """
    Python wrapper class for IES ClassOfClassOfElement
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str = None, classes: list[str] | None = None):
        """
            Instantiate the IES ClassOfClassOfElement

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES ClassOfClassOfElement
                classes (list): the IES types to instantiate

            Returns:
                ClassOfClassOfElement:
        """
        if classes is None:
            classes = [CLASS_OF_CLASS_OF_ELEMENT]
        super().__init__(tool=tool, uri=uri, classes=classes)


class ParticularPeriod(Element):
    """
    Python wrapper class for IES ParticularPeriod
    """

    def __init__(self, tool: IESTool = IES_TOOL, classes: list[str] | None = None, time_string: str = None):
        """
            Instantiate the IES ParticularPeriod

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                classes (list): the IES types to instantiate
                time_string (string): the ISO8601 representation of the period (no spaces - use T, Zulu)
            Returns:
                ParticularPeriod:
        """
        if classes is None:
            classes = [PARTICULAR_PERIOD]
        if not time_string:
            raise Exception("No time_string provided for ParticularPeriod")

        iso8601_time_string = time_string.replace(" ", "T")
        uri = f"http://iso.org/iso8601#{str(iso8601_time_string)}"

        super().__init__(tool=tool, uri=uri, classes=classes)

        self.add_literal(predicate=f"{IES_BASE}iso8601PeriodRepresentation",
                         literal=str(iso8601_time_string))


class BoundingState(State):
    """
    Python wrapper class for IES BoundingState
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES BoundingState

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES BoundingState
                classes (list): the IES types to instantiate

            Returns:
                BoundingState:
        """

        if classes is None:
            classes = [BOUNDING_STATE]
        super().__init__(tool=tool, uri=uri, classes=classes)


class BirthState(BoundingState):
    """
    Python wrapper class for IES BirthState
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES BirthState

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES BirthState
                classes (list): the IES types to instantiate

            Returns:
                BirthState:
        """

        if classes is None:
            classes = [BIRTH_STATE]
        super().__init__(tool=tool, uri=uri, classes=classes)


class DeathState(BoundingState):
    """
    Python wrapper class for IES DeathState
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None):
        """
            Instantiate the IES DeathState

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES DeathState
                classes (list): the IES types to instantiate

            Returns:
                DeathState:
        """

        if classes is None:
            classes = [DEATH_STATE]
        super().__init__(tool=tool, uri=uri, classes=classes)


class UnitOfMeasure(ClassOfClassOfElement):
    """
    Python wrapper class for IES UnitOfMeasure
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str = None, classes: list[str] | None = None):
        """
            Instantiate the IES UnitOfMeasure

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES UnitOfMeasure
                classes (list): the IES types to instantiate

            Returns:
                UnitOfMeasure:
        """

        if classes is None:
            classes = [UNIT_OF_MEASURE]
        super().__init__(tool=tool, classes=classes, uri=uri)


class Representation(ClassOfElement):
    """
    Python wrapper class for IES Representation
    """

    def __init__(self, tool: IESTool = IES_TOOL, representation_text: str | None = None, uri: str | None = None,
                 classes: list[str] | None = None, naming_scheme: NamingScheme | None = None):
        """
            Instantiate the IES Representation

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                representation_text (str): The exemplar text of the Representation
                uri (str): the URI of the IES Representation
                classes (list): the IES types to instantiate
                naming_scheme (NamingScheme): the IES NamingScheme the representation belongs to
            Returns:
                Representation:
        """

        if classes is None:
            classes = [REPRESENTATION]

        super().__init__(tool=tool, uri=uri, classes=classes)

        if representation_text:
            self.tool.add_triple(subject=self._uri, predicate=f"{IES_BASE}representationValue",
                                 obj=representation_text, is_literal=True, literal_type="string")
        if naming_scheme:
            self.tool.add_triple(subject=self._uri, predicate=f"{IES_BASE}inScheme",
                                 obj=naming_scheme.uri)


class WorkOfDocumentation(Representation):
    """
    Python wrapper class for IES WorkOfDocumentation
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None,
                 classes: list[str] | None = None):
        """
            Instantiate the IES WorkOfDocumentation

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Representation
                classes (list): the IES types to instantiate

            Returns:
                WorkOfDocumentation:
        """

        if classes is None:
            classes = [WORK_OF_DOCUMENTATION]

        super().__init__(tool=tool, uri=uri, classes=classes)


class MeasureValue(Representation):
    """
    Python wrapper class for IES MeasureValue
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 value: str | None = None, uom: UnitOfMeasure | None = None, measure: Measure | None = None):
        """
            Instantiate the IES MeasureValue

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES MeasureValue
                classes (list): the IES types to instantiate
                value (str): the value of the measure as a literal
                uom (UnitOfMeasure): the unit of measure of this value
                measure (Measure): the IES measure this is a value for
            Returns:
                MeasureValue:
        """

        if classes is None:
            classes = [MEASURE_VALUE]
        if not value:
            raise Exception("MeasureValue must have a valid value")
        super().__init__(tool=tool, representation_text=value, uri=uri, classes=classes, naming_scheme=None)
        if uom is not None:
            self.tool.add_triple(self._uri, f"{IES_BASE}measureUnit", obj=uom._uri)
        if measure is None:
            logger.warning("MeasureValue created without a corresponding measure")
        else:
            self.tool.add_triple(subject=measure._uri, predicate=f"{IES_BASE}hasValue",
                                 obj=self._uri)


class Measure(ClassOfElement):
    """
    Python wrapper class for IES Measure
    """

    def __init__(
            self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
            value: str = None, uom: UnitOfMeasure | None = None):
        """
            Instantiate the IES Measure

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Measure
                classes (list): the IES types to instantiate
                value (str): the value of the measure as a literal
                uom (UnitOfMeasure): the unit of measure of the value applied to this measure
        """
        self.measurements_map = {
            "Length": "ValueInMetres",
            "Mass": "ValueInKilograms",
            "Duration": "ValueInSeconds",
            "ElectricCurrent": "ValueInAmperes",
            "Temperature": "ValueInKelvin",
            "AmountOfSubstance": "ValueInMoles",
            "LuminousIntensity": "ValueInCandela"
        }

        if classes is None:
            classes = [MEASURE]
        if len(classes) != 1:
            logger.warning("Measure must be just one class, using the first one")
        _class = classes[0]

        super().__init__(tool=tool, uri=uri, classes=classes)
        value = str(value)
        value_class = (f"{IES_BASE}"
                       f"{self.measurements_map.get(_class.replace(IES_BASE, ''), MEASURE_VALUE[len(IES_BASE):])}"
                       )
        if value_class != MEASURE_VALUE and uom is not None:
            logger.warning("Standard measure: " + value_class + " do not require a unit of measure")

        MeasureValue(tool=self.tool, value=value, uom=uom, measure=self, classes=[value_class])


class Identifier(Representation):
    """
    Python wrapper class for IES Identifier
    """

    def __init__(
            self, tool: IESTool = IES_TOOL, id_text="", uri: str | None = None, classes: list[str] | None = None,
            naming_scheme: NamingScheme = None
    ):
        """
            Instantiate the IES Identifier

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Identifier
                classes (list): the IES types to instantiate
                naming_scheme (NamingScheme): the IES NamingScheme the Identifier belongs to
            Returns:
                Identifier:
        """

        if classes is None:
            classes = [IDENTIFIER]
        super().__init__(tool=tool, uri=uri, classes=classes, representation_text=id_text, naming_scheme=naming_scheme)


class Name(Representation):
    """
    Python wrapper class for IES Name
    """

    def __init__(self, tool: IESTool = IES_TOOL, name_text="", uri: str | None = None,
                 classes: list[str] | None = None, naming_scheme: NamingScheme = None):
        """
            Instantiate the IES Name

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Name
                classes (list): the IES types to instantiate
                naming_scheme (NamingScheme): the IES NamingScheme the Name belongs to
            Returns:
                Name:
        """

        if classes is None:
            classes = [NAME]

        super().__init__(
            tool=tool, uri=uri, classes=classes, representation_text=name_text, naming_scheme=naming_scheme
        )


class NamingScheme(ClassOfClassOfElement):
    """
    Python wrapper class for IES NamingScheme
    """

    def __init__(self, tool: IESTool = IES_TOOL, owner: ResponsibleActor | None = None, uri: str | None = None,
                 classes: list[str] | None = None):
        """
            Instantiate the IES NamingScheme

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                owner (ResponsibleActor): The actor responsible for this naming scheme
                uri (str): the URI of the IES NamingScheme
                classes (list): the IES types to instantiate
            Returns:
                NamingScheme:
        """
        if classes is None:
            classes = [NAMING_SCHEME]
        super().__init__(tool=tool, uri=uri, classes=classes)
        if owner is not None:
            self.tool.add_triple(
                subject=self._uri, predicate=f"{IES_BASE}schemeOwner", obj=owner._uri
            )

    def add_mastering_system(self, system: Entity):
        if system is not None:
            self.tool.add_triple(
                subject=self._uri, predicate=f"{IES_BASE}schemeMasteredIn", obj=system._uri
            )


class Event(Element):
    """
    Python wrapper class for IES class Event
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES Event

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Event
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Event
                end (str): an ISO8601 datetime string that marks the end of the Event

            Returns:
                Event:
        """

        if classes is None:
            classes = [EVENT]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

    def add_participant(self,
                        participating_entity: Entity | str,
                        uri: str | None = None,
                        participation_type: str | None = None,
                        start: str | None = None,
                        end: str | None = None
                        ) -> EventParticipant:
        """
        Adds a participant to the Event

        Args:
            participating_entity (Entity | str): The Entity (or uri ref to it) that is participating
            uri (str | None, optional): use to override participant uri. Defaults to None.
            participation_type (str | None, optional): use to override participation type.
            Defaults to ies:EventParticipant.
            start (str | None, optional): an ISO8601 datetime string that marks the start of the participation.
            Defaults to None.
            end (str | None, optional): an ISO8601 datetime string that marks the end of the participation.
            Defaults to None.

        Returns:
            EventParticipant:
        """

        pe_object = self._validate_referenced_object(participating_entity, Entity, "add_participant")

        if uri is None:
            uri = self.tool.generate_data_uri()

        if participation_type is None:
            participation_type = f"{IES_BASE}EventParticipant"

        participant = EventParticipant(tool=self.tool, uri=uri, start=start, end=end, classes=[participation_type])

        self.tool.add_triple(participant._uri, f"{IES_BASE}isParticipantIn", self._uri)
        self.tool.add_triple(participant._uri, f"{IES_BASE}isParticipationOf", pe_object._uri)
        return participant


class EventParticipant(State):
    """
    Python wrapper class for IES EventParticipant
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES EventParticipant

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES EventParticipant
                classes (list): the IES types to instantiate (default is ies:EventParticipant)
                start (str): an ISO8601 datetime string that marks the start of the EventParticipant
                end (str): an ISO8601 datetime string that marks the end of the EventParticipant

            Returns:
                EventParticipant:
        """

        if classes is None:
            classes = [EVENT_PARTICIPANT]
        super().__init__(tool=tool, start=start, end=end, uri=uri, classes=classes)


class Communication(Event):
    """
    Python wrapper class for IES Communication
    """

    def __init__(self, tool: IESTool = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None,
                 message_content: str | None = None):
        """
            Instantiate the IES Communication

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Communication
                classes (list): the IES types to instantiate
                start (str): an ISO8601 datetime string that marks the start of the Communication
                end (str): an ISO8601 datetime string that marks the end of the Communication
                message_content (str): the content of the communication as text
            Returns:
                Communication:
        """

        if classes is None:
            classes = [COMMUNICATION]
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        if message_content:
            self.add_literal(f"{IES_BASE}messageContent", message_content)

    def create_party(self, uri: str | None = None, party_role: str | None = None, start: str | None = None,
                     end: str | None = None) -> PartyInCommunication:
        """Creates a PartyInCommunication instance and relates it to the Communication instance

        Args:
            uri (str | None, optional): Set this to use a specific URI for the PartyInCommunication. Defaults to None.
            party_role (str | None, optional): Use this to select a subclass of PartyInCommunication. Defaults to None.
            start (str | None, optional): ISO8601 string - the start of the party's involvement. Defaults to None.
            end (str | None, optional): ISO8601 string - the end of the party's involvement. Defaults to None.

        Returns:
            PartyInCommunication: the PartyInCommunication instance
        """
        party_role = party_role or f"{IES_BASE}PartyInCommunication"

        if party_role not in self.tool.ontology.pic_subtypes:
            logger.warning(f"{party_role} is not a subtype of ies:PartyInCommunication")

        party = PartyInCommunication(tool=self.tool, uri=uri, communication=self,
                                     start=start, end=end, classes=[party_role])

        return party

    def add_party(self, uri: str | None = None, party_role: str | None = None, starts_in: str | None = None,
                  ends_in: str | None = None) -> PartyInCommunication:
        """DEPRECATED - USE create_party().

        Args:
            uri (str | None, optional): Set this  to use a specific URI for the PartyInCommunication. Defaults to None.
            party_role (str | None, optional): Use this to select a subclass of PartyInCommunication. Defaults to None.
            starts_in (str | None, optional): ISO8601 string - the start of the party's involvement. Defaults to None.
            ends_in (str | None, optional): ISO8601 string - the end of the party's involvement. Defaults to None.

        Returns:
            PartyInCommunication: the PartyInCommunication instance
        """
        logger.warning("add_party() is deprecated - please use create_party()")
        return self.add_party(uri=uri, party_role=party_role, starts_in=starts_in, ends_in=ends_in)


class PartyInCommunication(Event):
    """
    Python wrapper class for IES PartyInCommunication
    """

    def __init__(self, tool: IESTool | None = IES_TOOL, uri: str | None = None, classes: list[str] | None = None,
                 communication: Event | None = None, start: str | None = None,
                 end: str | None = None):
        """
            Instantiate the IES PartyInCommunication

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES PartyInCommunication
                classes (list): the IES types to instantiate (default is ies:PartyInCommunication)
                communication (Communication): the IES Communication the party is in
                start (str): an ISO8601 datetime string that marks the start of the PartyInCommunication
                end (str): an ISO8601 datetime string that marks the end of the PartyInCommunication
            Returns:
                PartyInCommunication:
        """

        if classes is None:
            classes = [PARTY_IN_COMMUNICATION]

        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)
        if communication is not None:
            communication.add_part(self)

    def add_account(self, account: Account | str, uri: str | None = None) -> EventParticipant:
        """
        Adds an Account to the PartyInCommunication

        Args:
            account (Account|str): the account (or referred URI) to add
            uri (str | None, optional): Use to override the uri of the created EventParticipant. Defaults to None.

        Returns:
            EventParticipant:
        """
        if uri is None:
            uri = self.tool._mint_dependent_uri(self.uri, "ACCOUNT")

        account_object = self._validate_referenced_object(account, Event, "add_account")

        try:

            aic = EventParticipant(
                tool=self.tool, uri=uri,
                classes=[f"{IES_BASE}AccountInCommunication"]
            )

            self.tool.add_triple(
                aic._uri,
                f"{IES_BASE}isParticipantIn",
                self._uri
            )

            self.tool.add_triple(
                aic._uri,
                f"{IES_BASE}isParticipationOf",
                account_object._uri
            )

            return aic

        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add account, no account will be added."
                f" {repr(e)}")

    def add_device(self, device: Device | str, uri: str | None = None) -> EventParticipant:
        """
        Adds a Device to the PartyInCommunication

        Args:
            device (Device | str): the Device (or referred URI) to add
            uri (str | None, optional): Use to override the uri of the created EventParticipant. Defaults to None.

        Returns:
            EventParticipant:
        """
        device_object = self._validate_referenced_object(device, Device, "add_device")
        if uri is None:
            uri = self.tool._mint_dependent_uri(self.uri, "DEVICE")
        try:
            dic = EventParticipant(
                tool=self.tool, uri=uri,
                classes=[f"{IES_BASE}DeviceInCommunication"]
            )
            self.tool.add_triple(
                dic._uri,
                f"{IES_BASE}isParticipantIn",
                self._uri)
            self.tool.add_triple(
                dic._uri,
                f"{IES_BASE}isParticipationOf",
                device_object._uri)


        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add device, no device will be added."
                f" {repr(e)}"
            )

        return dic

    def add_person(self, person: Person | str, uri: str | None = None) -> EventParticipant:
        """
        Adds a Person to the PartyInCommunication

        Args:
            person (Person | str): the Person (or referred URI) to add
            uri (str | None, optional): Use to override the uri of the created EventParticipant. Defaults to None.

        Returns:
            EventParticipant:
        """
        person_object = self._validate_referenced_object(person, Person, "add_person")
        if uri is None:
            uri = self.tool._mint_dependent_uri(self.uri, "PERSON")
        try:
            pic = EventParticipant(
                tool=self.tool, uri=uri,
                classes=[f"{IES_BASE}PersonInCommunication"]
            )
            self.tool.add_triple(
                pic._uri,
                f"{IES_BASE}isParticipantIn",
                self._uri)
            self.tool.add_triple(
                pic._uri,
                f"{IES_BASE}isParticipationOf",
                person_object._uri)
            return pic
        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add person, no person will be added."
                f" {repr(e)}"
            )


IES_TOOL = IESTool()
