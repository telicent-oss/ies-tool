from __future__ import annotations

import io
import json
import logging
import os
import pathlib
import uuid
import warnings
from typing import TypeVar

import requests
from geohash_tools import encode
from pyshacl import validate as pyshacl_validate
from rdflib import XSD, Graph, Literal, Namespace, URIRef

from ies_tool.ies_ontology import IES_BASE, Ontology
from ies_tool.ies_plugin import IESPlugin

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

ies_ns = Namespace(IES_BASE)
iso3166_ns = Namespace("http://iso.org/iso3166#")
iso8601_ns = Namespace("http://iso.org/iso8601#")

RdfsClassType = TypeVar('RdfsClassType', bound='RdfsClass')
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDFS_RESOURCE = "http://www.w3.org/2000/01/rdf-schema#Resource"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_CLASS = "http://www.w3.org/2000/01/rdf-schema#Class"
EXCHANGED_ITEM = f"{IES_BASE}ExchangedItem"
ELEMENT = f"{IES_BASE}Element"
CLASS_OF_ELEMENT = f"{IES_BASE}#ClassOfElement"
CLASS_OF_CLASS_OF_ELEMENT = f"{IES_BASE}#ClassOfClassOfElement"
PARTICULAR_PERIOD = f"{IES_BASE}ParticularPeriod"
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

logger = logging.getLogger(__name__)


class IESTool:
    """
    IESTool is a Python library for working with the UK Government Information Exchange Standard. This is the main class
    you need to initialise to start creating IES RDF data.

    The idea with this library is that you instantiate the IESTool class once - don't keep creating it, as there is some
    overhead in this. Instead, the idea is that you just run clear_graph every time you want to cycle out a new set
    of data.

    Instances of the IESTool class hold an in-memory copy of the IES ontology in an
    [rdflib](https://github.com/RDFLib/rdflib) graph which can be accessed through self.ontology.graph

    IESTool can work with in-memory data (e.g. with rdflib) or can connect to a SPARQL compliant triplestore and
    manipulate data in that dataset.
    """

    def __init__(
            self, uri_stub: str = "http://example.com/rdf/testdata#", mode: str = "rdflib",
            plug_in: IESPlugin | None = None, validate: bool = False, server_host: str = "http://localhost:3030/",
            server_dataset: str = "ds", default_security_label: str = ""
    ):
        """

        Args:
            uri_stub (str): The default URI path used for generating node URIs
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
            "byte",	 # -128…+127 (8 bit)
            "short",  # -32768…+32767 (16 bit)
            "int",  # -2147483648…+2147483647 (32 bit)
            "long",	 # -9223372036854775808…+9223372036854775807 (64 bit)
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
            self.__register_plugin(mode, plug_in)

        if self.__mode == "plugin":
            logger.info("Using a user-defined storage plugin")
            if validate:
                logger.warning("IES Tool cannot validate unless in 'rdflib' mode")
                self.__validate = False
        elif mode == "rdflib" and validate:
            if not validate:
                logger.warning('Enabling validation for rdflib mode')
            self.__validate = True
            self.__init_shacl(os.path.join(self.current_dir, "ies_r4_2_0.shacl"))
            logger.info("IES Tool set to validate all messages. This might get a bit slow")
        elif mode == "sparql_server":
            self.server_host = server_host
            self.server_dataset = server_dataset
            self.default_security_label = default_security_label
            try:
                query = "SELECT * WHERE { ?s ?p ?o } LIMIT 2"
                get_uri = self.server_host+self.server_dataset+"/query?query="+query
                requests.get(get_uri)
            except ConnectionError as e:
                raise RuntimeError(f"Could not connect to SPARQL endpoint at {self.server_host}") from e

        logger.debug("initialising data graph")

        # Note that both plugin and rdflib datasets are initialised to enable quick changeover
        self.graph = Graph()

        self.prefixes = {}
        self.uri_stub = uri_stub
        # Establish a set of useful prefixes
        self.add_prefix("xsd:", "http://www.w3.org/2001/XMLSchema#")
        self.add_prefix("dc:", "http://purl.org/dc/elements/1.1/")
        self.add_prefix("rdf:", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.add_prefix("rdfs:", "http://www.w3.org/2000/01/rdf-schema#")
        self.add_prefix("owl:", "http://www.w3.org/2002/07/owl#")
        self.add_prefix("iso8601:", "http://iso.org/iso8601#")
        self.add_prefix("iso3166:", "http://iso.org/iso3166#")
        self.add_prefix("ies:", IES_BASE)

        if self.__mode != "sparql_server":
            self.clear_graph()

        self.ies_uri_stub = IES_BASE
        self.iso8601_uri_stub = "http://iso.org/iso8601#"
        self.rdf_type = f"{self.prefixes['rdf:']}type"
        self.rdfs_resource = f"{self.prefixes['rdfs:']}Resource"
        self.rdfs_comment = f"{self.prefixes['rdfs:']}comment"
        self.rdfs_label = f"{self.prefixes['rdfs:']}label"

        self.__validate = False

        #Create a layered dictionary of base classes, along with their corresponding IES subclasses.
        #This enables look up of most appropriate base class when call instantiate
        #This may be better if it was in the ies_ontology library, but they don't have access to
        # the class definitions and didn't want to create a circular dependency...again
        self.base_classes = self.__all_python_subclasses({},RdfsResource,0)

    @property
    def uri_stub(self):
        return self.prefixes[":"]

    @uri_stub.setter
    def uri_stub(self,value):
        self.add_prefix(":",value)

    def add_prefix(self, prefix: str, uri: str):
        """
        Adds an RDF prefix to the internal list of namespace prefixes. If using rdflib for the in-memory graph,
        it will also register the namespace there

        Args:
            prefix (str): The prefix to add
            uri (str): The corresponding namespace URI
        """

        if ":" not in prefix:
            prefix = prefix + ":"

        self.prefixes[prefix] = uri
        if self.__mode == "rdflib":
            ns = Namespace(uri)
            self.graph.bind(prefix.replace(":",""), ns)

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

    #Creates a tiered dictionary (with integer keys for each tier).
    #Each tier has a dictionary of base classes, keyed by their equivalent IES Class URI
    #Each leaf object also holds a reference to the Python class and all the IES subclasses
    def __all_python_subclasses(self,hierarchy,cls,level):
        if level not in hierarchy:
            hierarchy[level] = {}
        uri = ''
        if "Rdfs" in cls.__name__:
            uri = cls.__name__.replace("Rdfs",RDFS)
        else:
            uri = IES_BASE+cls.__name__
        ies_subs = self.ontology.make_results_set_from_query(
            "SELECT ?p WHERE {?p <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + uri + ">}", "p")
        hierarchy[level][uri] = {'python_class':cls,'ies_subclasses':list(ies_subs)}
        subclasses = cls.__subclasses__()
        if len(subclasses) > 0:
            for sub in subclasses:
                self.__all_python_subclasses(hierarchy,sub,level+1)
        return hierarchy

    #Given an IES or RDFS class, this function will attempt to return the most appropriate base class
    # (and its level identifier)
    def __determine_base_class(self,classes):
        keys = reversed(self.base_classes.keys())
        for level_number in keys:
            level = self.base_classes[level_number]
            for bc in level:
                base_class = level[bc]
                for cls in classes:
                    if cls in base_class['ies_subclasses']:
                        return(base_class["python_class"],level_number)
        return self.base_classes[0]["python_class"],0


    def __get_instance(self, uri: str) -> RdfsResource | None:
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
            logger.warning("no instance with a uri: {uri}")
            return None

    def __register_plugin(self, plugin_name: str, plugin: IESPlugin | None):
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
            self.plug_in: IESPlugin | None = plugin
            self.plug_in.set_classes(self.ontology.classes)
            self.plug_in.set_properties(self.ontology.properties)

    def __init_shacl(self, shacl_filename: str):
        logger.info("parsing SHACL rules")
        self.shacl = Graph()
        self.shacl.parse(shacl_filename)
        logger.info("SHACL ready")



    def clear_graph(self) -> uuid.UUID:
        """
        Clears the graph currently in use

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
                self.graph.bind(prefix.replace(":",""),self.prefixes[prefix])
        self.session_uuid = uuid.uuid4()
        self.session_uuid_str = str(self.session_uuid)
        self.session_instance_count = 0
        self.instances = {}
        return self.session_uuid

    def set_uri_stub(self, uri_stub: str):
        """
        IES Tool maintains a default URI stub (namespace) for the data you're creating - this is used when generating
        UUID-based URIs.

        Args:
            uri_stub (str): The URI stub to add.
        """

        self.uri_stub = uri_stub
        self.add_prefix("data", uri_stub)

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

    def make_results_list_from_query(self, query: str, sparql_var_name: str):
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

    def run_sparql_query(self, query: str):
        """
        Runs a SPARQL query on the data - DOES NOT WORK ON plugins (yet)

        Args:
            query (str): The query to run
        """

        if self.__mode == "sparql_server":
            get_uri = self.server_host+self.server_dataset+"/query"
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
    def __str(_input: str | Graph):
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
    def __prep_object(obj: str, is_literal: bool, literal_type: str):
        """
        Checks the type of object place in an RDF triple and formats it for use in a SPARQL query

        Args:
            obj (str) - the RDF object (third position in an RDF triple)
            is_literal (bool) - set to true if passing a literal object
            literal_type (str) - an XML schema datatype
        """
        if is_literal:
            o = f'"{obj}"'
            if literal_type:
                o = f'{o}^^{literal_type}'
        else:
            o = f'<{obj}>'
        return o

    def __prep_spo(self, subject: str, predicate: str, obj: str, is_literal: bool = True,
                   literal_type: str | None = None):
        """
            Formats an RDF triple so it can be used in a SPARQL query or update

            Args:
                subject - the first position of the triple
                predicate - the second position of the triple
                obj - the third position of the triple
                is_literal - set to true if the third position is a literal
                literal_type - if the third position is a literal, set its XML datatype
        """
        return f"<{subject}> <{predicate}> {self.__prep_object(obj, is_literal, literal_type)}"

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
            self.clear_graph()

    def get_rdf(self, rdf_format: str = "nt", clear: bool = False):
        """
        Returns the RDF in the format requested. Note this only applies if in rdflib mode, or if the storage plugin
        supports data export

        Args:
            rdf_format (str): The requested rdf format (default is "nt" for n-triples)
            clear (bool): Whether to clear the graph after export of the data
        :return:
        """

        ret_dict = {
            "session_uuid": self.session_uuid,
            "triples": "",
            "validation_errors": ""
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

    def save_rdf(self, filename, format: str = "nt", clear: bool = False):
        """
        Saves the data in the RDF format choses

        Args:
            filename (str): The full file name to write out to
            format (str): The format of the saved RDF (default is "nt" for n-triples)
            clear (bool): Whether to clear the graph after saving
        """

        with open(filename, "w") as text_file:
            ret_dict = self.get_rdf(rdf_format=format, clear=clear)
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
            f'ASK {{ <> <>  {self.__prep_object(obj, is_literal, literal_type)}}}'
        else:
            if is_literal:
                return (URIRef(subject), URIRef(predicate), Literal(obj)) in self.graph
            else:
                return (URIRef(subject), URIRef(predicate), Literal(obj)) in self.graph

    def generate_data_uri(self, context: str = ""):
        """
        Creates a random (UUID) appended to the default uri_stub namespace in use

        Args:
            context (str): an additional string to insert into the URI to provide human-readable context
        """

        uri = f'{self.uri_stub}{self.session_uuid_str}{context}-{str(self.session_instance_count)}'
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
            update = f'DELETE DATA {{{self.__prep_spo(subject, predicate, obj, is_literal)}}}'
            self.run_sparql_update(update)
        return True

    def add_to_graph(self, subject: str, predicate: str, obj: str, is_literal: bool = False,
                     literal_type: str = "string", security_label: str = "") -> bool:
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

        if self.__mode == "plugin":
            self.plug_in.add_triple(
                subject=subject, predicate=predicate, obj=obj, is_literal=is_literal, literal_type=literal_type
            )
            return True
        elif self.__mode == "sparql_server":
            triple = self.__prep_spo(subject, predicate, obj, is_literal, literal_type)
            query = f'INSERT DATA {{{triple}}}'
            self.run_sparql_update(query=query, security_label=security_label)
        elif not self.in_graph(
                subject=subject, predicate=predicate, obj=obj, is_literal=is_literal, literal_type=literal_type
        ):
            # See is someone has passed a rdflib type and fix it
            subject = self.__str(subject)
            predicate = self.__str(predicate)
            obj = self.__str(obj)

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

    def add_literal(self, subject: str, predicate: str, obj: str, literal_type: str = "string"):
        """
        Adds a triple where the object is a literal

        Args:
            subject (str): The subject of the triple to add
            predicate (str): The predicate of the triple to add
            obj (str): The object of the triple to add
            literal_type: the XML datatype to use (default is "string")
        """
        return self.add_to_graph(subject, predicate, obj, is_literal=True, literal_type=literal_type)



    def instantiate(self, classes: list | None = None, uri: str = None, instance_uri_context: str = "",
                    base_class: RdfsResource | None = None):
        """
        Instantiates a list of classes

        Args:
            classes (list | None): The classes to instantiate (a single instance, of multiple classes).
            uri (str): The URI of the instance (if not set, one will be generated)
            instance_uri_context (str): an additional string to insert into the URI to provide human-readable
            context if no URI is provided
            base_class (RdfsResource): The base Python class to use (default is RdfsResource)
        """

        if classes is None or classes == []:
            classes = [RDFS_RESOURCE]

        if not isinstance(classes, list):
            raise RuntimeError(
                "instaniate() expects a list of classes - if you want to instantiate just one class,"
                " make a singleton list"
            )
        if base_class is None:
            base_class,level = self.__determine_base_class(classes)

        if uri is None:
            # Make an uri based on the data stub...
            uri = self.generate_data_uri(instance_uri_context)

        cls_str: str = ""

        classes.sort()
        # If we have more than one class, we make a new class name by concatenating the class names

        for cls in classes:
            cls_name = cls.replace(self.ies_uri_stub, "")
            cls_str = f"{cls_str}{cls_name}"

        return base_class(uri=uri, tool=self)

    def create_event(self, uri: str | None = None, classes: list | None = None,
                     event_start: str | None = None, event_end: str | None = None,
                     ) -> Event:
        """
        Instantiate an IES Event.

        Args:
            uri (str): The URI for the event
            classes (list): a list of IES classes that it will be a member of
            event_start (str): The start of the event as an ISO8601 string (no spaces - use a T)
            event_end (str): The end of the event as an ISO8601 string (no spaces - use a T)

        Returns:
            Event: The created Event wrapped as an IES Event class
        """

        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#Event"]

        event = Event(
            tool=self, start=event_start, end=event_end, uri=uri, classes=classes
        )
        return event

    def create_person(self, uri: str | None = None, classes: list | None = None,
                      given_name: str | None = None, family_name: str | None = None, dob: str | None = None,
                      pob: Location | None = None, dod: str | None = None, pod: Location | None = None) -> Person:
        """
        Instantiate an IES Person

        Args:
            given_name (str): first name of the person
            family_name (str): surname of the person
            dob (str): date of birth of the person (ISO8601 string, no spaces, use T)
            pob (Location): place of birth of the person a Python Location object
            classes (list): the IES types to instantiate  - default is Person - shouldn't need to change this
            uri (str): the URI of the Person instance - if unset, one will be created.
            dod (str): date of death of the person (ISO8601 string, no spaces, use T)
            pod (Location): place of death of the person a Python Location object

        Returns:
            Person: a Python Person object that wraps the IES Person data
        """
        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#Person"]

        person = Person(
            tool=self, family_name=family_name, given_name=given_name, start=dob, pob=pob, uri=uri, end=dod, pod=pod,
            classes=classes
        )

        return person

    def create_measure(self, uri: str | None = None, classes: list | None = None,
                       value: str | None = None, uom: UnitOfMeasure | None = None) -> Measure:
        """
        Creates a measure that's an instance of a given measureClass, adds its value and unit of measure.

        Args:
            uri (str): the URI of the Measure instance
            classes (list):the IES types to instantiate  - default is Measure
            value (Str): the value of the measure
            uom (UnitOfMeasure): the unit of measure

        Returns:
            Measure - the instance created wrapped as a Python object
        """
        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#Measure"]

        measure = Measure(
            tool=self, value=value, uom=uom, uri=uri, classes=classes
        )
        return measure

    def create_communication(self, uri: str | None = None, classes: list | None = None,
                             starts_in: str | None = None, ends_in: str | None = None,
                             message_content: str | None = None) -> Communication:
        """
        Instantiates an IES Communication class

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

        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#Communication"]

        communication = Communication(
            tool=self, uri=uri, classes=classes, start=starts_in, end=ends_in,
            message_content=message_content
        )
        return communication

    def create_geopoint(
            self, uri: str | None = None, classes: list | None = None,
            lat: float | None = None, lon: float | None = None, precision: int | None = 6
    ) -> GeoPoint:
        """
        Creates instance of GeoPoint object.

        Args:
            uri (str): the URI of the GeoPoint instance
            classes (list): the IES types to instantiate  - default is GeoPoint
            lat (float): the latitude of the geopoint
            lon (float): the longitude of the geopoint
            precision (int): the precision of the lat lon in decimal places and hence also the produced geohash

        Returns:
            GeoPoint - instance wrapped as a Python GeoPoint object
        """

        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#GeoPoint"]

        for _class in classes:
            if _class not in self.ontology.geopoint_subtypes:
                logger.warning(f"{_class} is not a subtype of ies:GeoPoint")
        return GeoPoint(
            tool=self, uri=uri, lat=lat, lon=lon, precision=precision, classes=classes
        )

    def create_organisation(self, uri: str | None = None, classes: list | None = None,
                            name: str | None = None) -> Organisation:
        """
        Create instance of Organisation object.

        Args:
            uri (str): the URI of the Organisation instance
            classes (list): the IES types to instantiate  - default is Organisation
            name (str): The name of the Organisation

        Returns:
            Organisation:
        """
        if classes is None:
            classes = ["http://ies.data.gov.uk/ontology/ies4#Organisation"]
        return Organisation(
            tool=self, name=name, uri=uri, classes=classes
        )


class Unique(type):
    def __call__(cls, *args, **kwargs):
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
            self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None
    ):
        """
            Instantiate the RDFS Resource

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the RDFS Resource
                classes (list): the IES types to instantiate

            Returns:
                RdfsResource:
        """
        if classes is None:
            classes = [RDFS_RESOURCE]
        if tool is None:
            raise RuntimeError("No IES Tool provided")
        else:
            self._tool = tool
        if not uri:
            self._uri = self._tool.generate_data_uri()
        else:
            self._uri = uri

        for cls in classes:
            self._tool.add_to_graph(subject=self._uri, predicate=RDF_TYPE, obj=cls)
        self._classes = classes

        self._tool.instances[self._uri] = self

    @property
    def tool(self):
        return self._tool

    @property
    def uri(self):
        return self._uri

    @property
    def labels(self):
        return self._tool.make_results_list_from_query(
            "SELECT ?l WHERE {<" + self._uri + "> <http://www.w3.org/2000/01/rdf-schema#label> ?l }", "l")

    @property
    def comments(self):
        return self._tool.make_results_list_from_query(
            "SELECT ?c WHERE {<" + self._uri + "> <http://www.w3.org/2000/01/rdf-schema#comment> ?c }", "c")

    def add_type(self, uri):
        self._tool.add_to_graph(self.uri, predicate=RDF_TYPE, obj=uri)

    # Adds a triple where the object is a literal
    def add_literal(self, predicate: str, obj: str, literal_type: str = "string"):
        return self._tool.add_to_graph(self._uri, predicate, obj, is_literal=True, literal_type=literal_type)

    def add_label(self, label):
        self.add_literal(predicate=self._tool.rdfs_label, obj=label)

    def add_comment(self, comment):
        self.add_literal(predicate=self._tool.rdfs_comment, obj=comment)

    def _validate_referenced_object(self,reference,base_type=None,context=""):
        if isinstance(reference,str):
            if reference in self._tool.instances:
                return self._tool.instances[reference]
            else:
                logger.warning(
                    f"String passed instead of object in {context} - will assume this is a valid URI: {reference}"
                )
                if base_type is None:
                    base_type = RdfsResource
                return base_type(tool=self._tool,uri=reference,classes=[])
        elif isinstance(reference,RdfsResource):
            return reference
        else:
            raise Exception(f"Unknown type {str(type(reference))} in {context}")

class RdfsClass(RdfsResource):
    """
        A Python wrapper class for RDFS Class
    """
    def __init__(
            self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None
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

    def instantiate(self, uri=None):
        self._tool.instantiate([self.uri], uri)

    def add_sub_class(self, sub_class: type[RdfsClassType]):
        pass


class ExchangedItem(RdfsResource):
    """
        A Python wrapper class for IES ExchangedItem
    """
    def __init__(
            self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None):
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
            self, representation_text, representation_class: str | None = f"{IES_BASE}Representation",
            uri: str | None = None, rep_rel_type: str | None = None, naming_scheme=None):
        if not rep_rel_type:
            rep_rel_type = "http://ies.data.gov.uk/ontology/ies4#isRepresentedAs"
        representation = Representation(
            tool=self._tool, representation_text=representation_text, uri=uri,
            classes=[representation_class], naming_scheme=naming_scheme
        )
        self._tool.add_to_graph(subject=self._uri, predicate=rep_rel_type, obj=representation._uri)
        return representation

    def add_name(
            self, name, name_class: str | None = f"{IES_BASE}Name", uri=None, name_rel_type=None,
            naming_scheme=None):
        if not name_rel_type:
            name_rel_type = "http://ies.data.gov.uk/ontology/ies4#hasName"

        representation = Name(
            tool=self._tool, name_text=name, uri=uri,
            classes=[name_class], naming_scheme=naming_scheme
        )
        self._tool.add_to_graph(subject=self._uri, predicate=name_rel_type, obj=representation._uri)

    def add_identifier(
            self, identifier, id_class: str | None = f"{IES_BASE}Identifier", uri=None, id_rel_type=None,
            naming_scheme=None):
        if not id_rel_type:
            id_rel_type = "http://ies.data.gov.uk/ontology/ies4#isIdentifiedBy"
        representation = Identifier(
            tool=self._tool, id_text=identifier, uri=uri, classes=[id_class], naming_scheme=naming_scheme
        )
        self._tool.add_to_graph(subject=self._uri, predicate=id_rel_type, obj=representation._uri)


class Element(ExchangedItem):
    """
        A Python wrapper class for IES Element
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
            classes = ["http://ies.data.gov.uk/ontology/ies4#Element"]

        super().__init__(tool=tool, uri=uri, classes=classes)
        self._default_state_type = "http://ies.data.gov.uk/ontology/ies4#State"

        if start:
            self.starts_in(start)
        if end:
            self.ends_in(end)

    def add_part(self, part, part_rel_type=None):
        """
            takes an Element instance and adds it as part of the current Element
        """
        part_object = self._validate_referenced_object(part,Element,"add_part")
        if part_rel_type is None:
            part_rel_type = "http://ies.data.gov.uk/ontology/ies4#isPartOf"
        self._tool.add_to_graph(part_object.uri, part_rel_type, self._uri)
        return part_object

    def add_state(
            self, state_type: str | None = None, uri: str | None = None,
            state_rel: str | None = None, start: str | None = None, end: str | None = None,
            in_location: Location | None = None
    ) -> State:
        """
        creates a state to an item (needs to be deprecated and replaced by create_state in next version)
        """
        if not state_type:
            state_type = self._default_state_type

        state = State(tool=self._tool, start=start, end=end, uri=uri, classes=[state_type])

        if not state_rel:
            state_rel = "http://ies.data.gov.uk/ontology/ies4#isStateOf"

        self._tool.add_to_graph(subject=state._uri, predicate=state_rel, obj=self._uri)

        if in_location is not None:
            state.in_location(in_location)
        return state

    def in_location(self, location):
        """
            places the Element in a Location
        """
        location_object = self._validate_referenced_object(location,Location,"in_location")
        self._tool.add_to_graph(
            subject=self.uri, predicate="http://ies.data.gov.uk/ontology/ies4#inLocation",
            obj=location_object.uri)
        return location_object

    def put_in_period(self, time_string: str):
        """
        Puts an item in a particular period
        """
        pp_instance = ParticularPeriod(tool=self._tool, time_string=time_string)
        self._tool.add_to_graph(self._uri, "http://ies.data.gov.uk/ontology/ies4#inPeriod", pp_instance._uri)
        return pp_instance

    def starts_in(self, time_string: str, bounding_state_class: str | None = None,
                  uri: str | None = None) -> BoundingState:
        """
        Asserts an item started in a particular period
        """
        if bounding_state_class is None:
            bounding_state_class = "http://ies.data.gov.uk/ontology/ies4#BoundingState"

        bs = BoundingState(tool=self._tool, classes=[bounding_state_class], uri=uri)
        self._tool.add_to_graph(subject=bs._uri, predicate="http://ies.data.gov.uk/ontology/ies4#isStartOf",
                                obj=self._uri)
        if time_string:
            bs.put_in_period(time_string=time_string)
        return bs

    def ends_in(self, time_string: str, bounding_state_class: str | None = None,
                uri: str | None = None) -> BoundingState:
        """
        Asserts an item ended in a particular period.
        """
        if bounding_state_class is None:
            bounding_state_class = "http://ies.data.gov.uk/ontology/ies4#BoundingState"

        bs = BoundingState(tool=self._tool, classes=[bounding_state_class], uri=uri)
        self._tool.add_to_graph(subject=bs._uri, predicate="http://ies.data.gov.uk/ontology/ies4#isEndOf",
                                obj=self._uri)
        if time_string:
            bs.put_in_period(time_string=time_string)
        return bs

    def add_measure(self, value, measure_class=None, uom=None, uri: str = None):
        measure = Measure(
            tool=self._tool, uri=uri, classes=[measure_class], value=value, uom=uom
        )
        self._tool.add_to_graph(
            subject=self._uri, predicate="http://ies.data.gov.uk/ontology/ies4#hasCharacteristic", obj=measure._uri
        )


class Entity(Element):
    """
        A Python wrapper class for IES Entity
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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


class Device(Entity):
    """
        A Python wrapper class for IES Device
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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


class Location(Entity):
    """
        A Python wrapper class for IES Location
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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


class GeoPoint(Location):
    """
    Python wrapper class for IES GeoPoint, with geo-hashes used to make the URI
    """

    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
                 lat: float = None, lon: float = None, precision: int = None,
                 start: str | None = None, end: str | None = None):
        """
            Instantiate the IES GeoPoint

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES GeoPoint
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
        super().__init__(tool=tool, uri=uri, classes=classes, start=start, end=end)

        self.my_hash = str(encode(float(lat), float(lon), precision=precision))

        self.id_uri_base = "http://geohash.org/"
        self.lat_uri = f"{self.id_uri_base}{self.my_hash}_LAT"
        self.lon_uri = f"{self.id_uri_base}{self.my_hash}_LON"

        self.add_identifier(identifier=str(lat), uri=self.lat_uri,
                            id_class="http://ies.data.gov.uk/ontology/ies4#Latitude")

        self.add_identifier(identifier=str(lon), uri=self.lon_uri,
                            id_class="http://ies.data.gov.uk/ontology/ies4#Longitude")


class ResponsibleActor(Entity):
    """
    Python wrapper class for IES ResponsibleActor
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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

        self._default_state_type = "http://ies.data.gov.uk/ontology/ies4#ResponsibleActorState"

    # Asserts the responsible actor works for another responsible actor
    def works_for(self, employer, start: str | None = None, end: str | None = None):
        employer_object = self._validate_referenced_object(employer,ResponsibleActor,"works_for")
        state = self.add_state(start=start, end=end)
        self._tool.add_to_graph(subject=state._uri, predicate="http://ies.data.gov.uk/ontology/ies4#worksFor",
                                obj=employer_object._uri)
        return state

    def in_post(self, post, start: str | None = None, end: str | None = None):
        post_object = self._validate_referenced_object(post,Post,"in_post")
        in_post = self.add_state(state_type="http://ies.data.gov.uk/ontology/ies4#InPost", start=start, end=end)
        post_object.add_part(in_post)
        return post_object


class Post(ResponsibleActor):
    """
    Python wrapper class for IES Post
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
                 start: str | None = None, end: str | None = None, family_name: str | None = None,
                 given_name: str | None = None, pob: Location | None = None,
                 pod: Location | None = None):
        """
            Instantiate the IES Person

            Args:
                tool (IESTool): The IES Tool which holds the data you're working with
                uri (str): the URI of the IES Person
                classes (list): the IES types to instantiate (default is ies:Person)
                start (str): an ISO8601 datetime string that marks the birth of the Person
                end (str): an ISO8601 datetime string that marks the death of the Person
                family_name (str): surname of the person
                given_name (str): the first name of the Person
                pob (Location): the place of birth of the Person
                pod (Location): the place of death of the Person
            Returns:
                Person:
        """
        if classes is None:
            classes = [PERSON]

        super().__init__(tool=tool, uri=uri, classes=classes, start=None, end=None)

        self._default_state_type = "http://ies.data.gov.uk/ontology/ies4#PersonState"

        if given_name:
            name_uri_firstname = f"{self._uri}_FIRSTNAME"
            self.add_name(given_name, uri=name_uri_firstname,
                          name_class="http://ies.data.gov.uk/ontology/ies4#GivenName")

        if family_name:
            name_uri_surname = f"{self._uri}_SURNAME"
            self.add_name(family_name, uri=name_uri_surname,
                          name_class="http://ies.data.gov.uk/ontology/ies4#Surname")

        if start is not None:
            self.add_birth(start, pob)

        if end is not None:
            self.add_death(end, pod)

    def add_birth(self, dob: str, pob = None) -> BoundingState:
        """

        :param dob: Date of birth represented as string
        :param pob:  Location of birth
        :return: BirthState object
        """

        birth_uri = f'{self._uri}_BIRTH'
        birth = self.starts_in(time_string=dob, bounding_state_class="http://ies.data.gov.uk/ontology/ies4#BirthState",
                               uri=birth_uri)
        if pob:
            pob_object = self._validate_referenced_object(pob,Location,"add_birth")
            self._tool.add_to_graph(birth._uri, "http://ies.data.gov.uk/ontology/ies4#inLocation", pob_object._uri)
        return birth

    def add_death(self, dod: str, pod = None, uri: str | None = None) -> BoundingState:
        """
        # Adds a death state and (optionally) a location of death to a being (usually a person)
        :param dod: Date of death represented as string
        :param pod: Location - to optionally specify place of death
        :param uri:
        :return: DeathState object
        """

        uri = uri or self._uri + "_DEATH"
        death = self.ends_in(
            dod, bounding_state_class="http://ies.data.gov.uk/ontology/ies4#DeathState", uri=uri
        )
        if pod:
            pod_object = self._validate_referenced_object(pod,Location,"add_death")
            self._tool.add_to_graph(death._uri, "http://ies.data.gov.uk/ontology/ies4#inLocation", pod_object._uri)

        return death


class Organisation(ResponsibleActor):
    """
    Python wrapper class for IES Organisation
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list | None = None,
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

        self._default_state_type = "http://ies.data.gov.uk/ontology/ies4#OrganisationState"

        if name is not None and name != "":
            self.add_name(name, name_class=ORGANISATION_NAME)

    def add_post(self, name, start: str | None = None, end: str | None = None, uri: str | None = None):
        post = Post(tool=self._tool, uri=uri, start=start, end=end)
        if name is not None and name != "":
            post.add_name(name)
        self.add_part(post)
        return post


class ClassOfElement(RdfsClass, ExchangedItem):
    """
    Python wrapper class for IES ClassOfElement
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None):
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

    def add_measure(self, value, measure_class: str | None = None, uom: UnitOfMeasure | None = None, uri: str = None):

        measure = Measure(
            tool=self._tool, value=value, uom=uom, uri=uri, classes=[measure_class]
        )
        self._tool.add_to_graph(subject=self._uri,
                                predicate="http://ies.data.gov.uk/ontology/ies4#allHaveCharacteristic",
                                obj=measure._uri)


class ClassOfClassOfElement(RdfsClass, ExchangedItem):
    """
    Python wrapper class for IES ClassOfClassOfElement
    """
    def __init__(self, tool: IESTool, uri: str = None, classes: list[str] | None = None):
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
    def __init__(self, tool: IESTool, classes: list[str] | None = None, time_string: str = None):
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

        self.add_literal(predicate="http://ies.data.gov.uk/ontology/ies4#iso8601PeriodRepresentation",
                         obj=str(iso8601_time_string))


class BoundingState(State):
    """
    Python wrapper class for IES BoundingState
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None):
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None):
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None):
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
    def __init__(self, tool: IESTool,  uri: str = None, classes: list[str] | None = None):
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
        super().__init__(tool=tool, classes=classes,  uri=uri)


class Representation(ClassOfElement):
    """
    Python wrapper class for IES Representation
    """

    def __init__(self, tool: IESTool, representation_text: str, uri: str | None = None,
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

        self._tool.add_to_graph(subject=self._uri, predicate="http://ies.data.gov.uk/ontology/ies4#representationValue",
                                obj=representation_text, is_literal=True, literal_type="string")
        if naming_scheme:
            self._tool.add_to_graph(subject=self._uri, predicate="http://ies.data.gov.uk/ontology/ies4#inScheme",
                                    obj=naming_scheme.uri)


class MeasureValue(Representation):
    """
    Python wrapper class for IES MeasureValue
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
        if value is None or value == "":
            raise Exception("MeasureValue must have a valid value")
        super().__init__(tool=tool, representation_text=value, uri=uri, classes=classes, naming_scheme=None)
        if uom is not None:
            self._tool.add_to_graph(self._uri, "http://ies.data.gov.uk/ontology/ies4#measureUnit", obj=uom._uri)
        if measure is None:
            logger.warning("MeasureValue created without a corresponding measure")
        else:
            self._tool.add_to_graph(subject=measure._uri, predicate="http://ies.data.gov.uk/ontology/ies4#hasValue",
                                    obj=self._uri)


class Measure(ClassOfElement):
    """
    Python wrapper class for IES Measure
    """
    def __init__(
            self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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

        if classes is None:
            classes = [MEASURE]
        if len(classes) != 1:
            logger.warning("Measure must be just one class, using the first one")
        _class = classes[0]

        super().__init__(tool=tool, uri=uri, classes=classes)
        value = str(value)
        if _class == "http://ies.data.gov.uk/ontology/ies4#Length":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInMetres"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#Mass":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInKilograms"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#Duration":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInSeconds"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#ElectricCurrent":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInAmperes"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#Temperature":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInKelvin"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#AmountOfSubstance":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInMoles"
        elif _class == "http://ies.data.gov.uk/ontology/ies4#LuminousIntensity":
            value_class = "http://ies.data.gov.uk/ontology/ies4#ValueInCandela"
        else:
            value_class = MEASURE_VALUE
        if value_class != MEASURE_VALUE and uom is not None:
            logger.warning("Standard measure: " + value_class + " do not require a unit of measure")

        MeasureValue(tool=self._tool, value=value, uom=uom, measure=self, classes=[value_class])


class Identifier(Representation):
    """
    Python wrapper class for IES Identifier
    """
    def __init__(
            self, tool: IESTool, id_text="", uri: str | None = None, classes: list[str] | None = None,
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
    def __init__(self, tool: IESTool, name_text="", uri: str | None = None,
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
    def __init__(self, tool: IESTool, owner: ResponsibleActor | None = None, uri: str | None = None,
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
            self._tool.add_to_graph(
                subject=self._uri, predicate="http://ies.data.gov.uk/ontology/ies4#schemeOwner", obj=owner._uri
            )

    def add_mastering_system(self, system: Entity):
        if system is not None:
            self._tool.add_to_graph(
                subject=self._uri, predicate="http://ies.data.gov.uk/ontology/ies4#schemeMasteredIn", obj=system._uri
            )


class Event(Element):
    """
    Python wrapper class for IES class Event
    """

    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
                        participating_entity,
                        uri: str | None = None,
                        participation_type: str | None = None,
                        start: str | None = None,
                        end: str | None = None
                        ) -> State:
        """
        Adds a participant to an event
        :param participating_entity:
        :param uri:
        :param participation_type:
        :param start:
        :param end:
        :return:
        """

        pe_object = self._validate_referenced_object(participating_entity,Entity,"add_participant")

        if uri is None:
            uri = self.tool.generate_data_uri()

        if participation_type is None:
            participation_type = "http://ies.data.gov.uk/ontology/ies4#EventParticipant"

        participant = EventParticipant(tool=self._tool, uri=uri, start=start, end=end, classes=[participation_type])

        self._tool.add_to_graph(participant._uri, "http://ies.data.gov.uk/ontology/ies4#isParticipantIn", self._uri)
        self._tool.add_to_graph(participant._uri, "http://ies.data.gov.uk/ontology/ies4#isParticipationOf",
                                pe_object._uri)
        return participant


class EventParticipant(State):
    """
    Python wrapper class for IES EventParticipant
    """
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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
            self.add_literal("http://ies.data.gov.uk/ontology/ies4#messageContent", message_content)

    def add_party(self, uri: str | None = None, party_role: str | None = None, starts_in: str | None = None,
                  ends_in: str | None = None) -> Event:
        party_role = party_role or "http://ies.data.gov.uk/ontology/ies4#PartyInCommunication"

        if party_role not in self._tool.ontology.pic_subtypes:
            logger.warning(f"{party_role} is not a subtype of ies:PartyInCommunication")

        party = PartyInCommunication(tool=self._tool, uri=uri, communication=self, start=starts_in, end=ends_in)

        return party


class PartyInCommunication(Event):
    """
    Python wrapper class for IES PartyInCommunication
    """

    def __init__(self, tool: IESTool, uri: str | None = None, classes: list[str] | None = None,
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

    def add_account(self, account, uri: str | None = None):

        uri = uri or self._uri + "-account"
        account_object = self._validate_referenced_object(account,Event,"add_account")
        try:
            aic = EventParticipant(
                tool=self._tool, uri=uri,
                classes=["http://ies.data.gov.uk/ontology/ies4#AccountInCommunication"]
            )
            self._tool.add_to_graph(
                aic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipantIn",
                self._uri)
            self._tool.add_to_graph(
                aic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipationOf",
                account_object._uri)
        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add account, no account will be added."
                f" {repr(e)}")
        return account_object

    def add_device(self, device, uri: str | None = None):
        device_object = self._validate_referenced_object(device,Device,"add_device")
        uri = uri or self._uri + "-account"
        try:
            dic = EventParticipant(
                tool=self._tool, uri=uri,
                classes=["http://ies.data.gov.uk/ontology/ies4#DeviceInCommunication"]
            )
            self._tool.add_to_graph(
                dic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipantIn",
                self._uri)
            self._tool.add_to_graph(
                dic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipationOf",
                device_object._uri)
        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add device, no device will be added."
                f" {repr(e)}"
            )
        return device_object

    def add_person(self, person, uri: str | None = None):
        person_object = self._validate_referenced_object(person,Person,"add_person")
        uri = uri or self._uri + "-account"
        try:
            pic = EventParticipant(
                tool=self._tool, uri=uri,
                classes=["http://ies.data.gov.uk/ontology/ies4#PersonInCommunication"]
            )
            self._tool.add_to_graph(
                pic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipantIn",
                self._uri)
            self._tool.add_to_graph(
                pic._uri,
                "http://ies.data.gov.uk/ontology/ies4#isParticipationOf",
                person_object._uri)
        except AttributeError as e:
            logger.warning(
                f"Exception occurred while trying to add person, no person will be added."
                f" {repr(e)}"
            )
        return person_object
