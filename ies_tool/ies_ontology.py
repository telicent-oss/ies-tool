from __future__ import annotations

import io
import json
import logging

from rdflib import Graph
from rdflib.plugins.sparql.results.jsonresults import JSONResultSerializer

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

logger = logging.getLogger()

IES_BASE = "http://ies.data.gov.uk/ontology/ies4#"


class Ontology:
    def __init__(self, filename: str | None = "./ies4.ttl"):
        """
        IES Tools stores a copy of the IES ontology as an RDFlib graph.
        It also caches properties and classes into simple Python lists
        This section loads the ontology, then gets all the rdfs:Classes and makes a dictionary of them (self.classes)
        """
        self.graph = Graph()
        self.classes = set()
        self.properties = set()
        self.datatype_properties = set()
        self.object_properties = set()
        self.graph.parse(filename)
        self.ies_uri_stub = IES_BASE

        logger.info("caching IES ontology")
        # Now create some caches of IES and related stuff we can use to warn the user
        # if they stray off the straight and narrow
        self.classes = self.make_results_set_from_query(
            "SELECT ?c WHERE {?c a <http://www.w3.org/2000/01/rdf-schema#Class>}", "c")
        self.properties = self.make_results_set_from_query(
            "SELECT ?p WHERE {?p a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property>}", "p")
        self.datatype_properties = self.make_results_set_from_query(
            "SELECT ?p WHERE {?p a <http://www.w3.org/2002/07/owl#DatatypeProperty>}", "p")
        self.object_properties = self.make_results_set_from_query(
            "SELECT ?p WHERE {?p a <http://www.w3.org/2002/07/owl#ObjectProperty>}", "p")

        self.__person_subtypes = self.make_results_set_from_query(
            "SELECT ?p WHERE {?p <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "Person") + ">}", "p")
        self.__organisation_subtypes = self.make_results_set_from_query(
            "SELECT ?p WHERE {?p <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "Organisation") + ">}", "p")
        self.__event_subtypes = self.make_results_set_from_query(
            "SELECT ?e WHERE {?e <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "Event") + ">}", "e")
        self.__communication_subtypes = self.make_results_set_from_query(
            "SELECT ?e WHERE {?e <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "Communication") + ">}", "e")
        self.geopoint_subtypes = self.make_results_set_from_query(
            "SELECT ?e WHERE {?e <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "GeoPoint") + ">}", "e")
        self.pic_subtypes = self.make_results_set_from_query(
            "SELECT ?e WHERE {?e <http://www.w3.org/2000/01/rdf-schema#subClassOf>* <" + self.ies_class(
                "PartyInCommunication") + ">}", "e")

        self.classes.add("http://www.w3.org/2000/01/rdf-schema#Class")
        self.classes.add("http://www.w3.org/2000/01/rdf-schema#Property")
        self.classes.add("http://www.w3.org/2002/07/owl#Class")
        self.object_properties.add("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
        self.datatype_properties.add("http://www.w3.org/2000/01/rdf-schema#label")
        self.datatype_properties.add("http://www.w3.org/2000/01/rdf-schema#comment")
        self.object_properties.add("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        self.object_properties.add("http://www.w3.org/2000/01/rdf-schema#subPropertyOf")
        self.properties.update(self.datatype_properties)
        self.properties.update(self.object_properties)

        # Now some shortcuts
        self.__ahc = self.ies_property("allHaveCharacteristic")
        self.__ep = self.ies_class("EventParticipant")
        self.__event = self.ies_class("Event")
        self.__given_name = self.ies_class("GivenName")
        self.__gp = self.ies_class("GeoPoint")
        self.__hc = self.ies_property("hasCharacteristic")
        self.__hn = self.ies_property("hasName")
        self.__hv = self.ies_property("hasValue")
        self.__id = self.ies_class("Identifier")
        self.__iib = self.ies_property("isIdentifiedBy")
        self.__il = self.ies_property("inLocation")
        self.__ipi = self.ies_property("isParticipantIn")
        self.__ipo = self.ies_property("isParticipationOf")
        self.__iso = self.ies_property("isStateOf")
        self.__measure = self.ies_class("Measure")
        self.__measure_value = self.ies_class("MeasureValue")
        self.__mu = self.ies_property("measureUnit")
        self.__name = self.ies_class("Name")
        self.__person = self.ies_class("Person")
        self.__rv = self.ies_property("representationValue")
        self.__surname = self.ies_class("Surname")
        self.__tpi = "http://telicent.io/ontology/primaryImage"
        self.datatype_properties.add(self.__tpi)
        self.__tpn = "http://telicent.io/ontology/primaryName"
        self.datatype_properties.add(self.__tpn)

        self.__communication = self.ies_class("Communication")
        self.__pic = self.ies_class("PartyInCommunication")

        logger.info("IES ontology ready")

    # runs a query on the ontology and returns the results
    def __run_query(self, query: str):
        results = self.graph.query(query)
        with io.StringIO() as f:
            JSONResultSerializer(results).serialize(f)
            return json.loads(f.getvalue())

    # pulls out individual variable from each row returned from sparql query. This is a bit niche, I know.
    def make_results_set_from_query(self, query: str, sparql_var_name: str):
        result_object = self.__run_query(query)
        return_set = set()
        if "results" in result_object.keys() and "bindings" in result_object["results"].keys():
            for binding in result_object["results"]['bindings']:
                return_set.add(binding[sparql_var_name]['value'])
        return return_set

        # pulls out individual variable from each row returned from sparql query. It's a bit niche, I know.
    def make_results_dict_from_query(self, query: str, sparql_var_name: str):
        result_object = self.__run_query(query)
        return_dict = {}
        if "results" in result_object.keys() and "bindings" in result_object["results"].keys():
            for binding in result_object["results"]['bindings']:
                return_dict[binding[sparql_var_name]['value']] = {}
        return return_dict

    # Returns the full IES URI for a provided short name of an IES class
    def ies_class(self, short_name: str):
        short_name.replace("ies:", "")  # just in case someone used the prefix

        if self.ies_uri_stub + short_name not in self.classes:
            logger.warning(f"class {short_name} not in IES ontology")

        return f"{self.ies_uri_stub}{short_name}"

    # Returns the full IES URI for a provided short name of an IES property
    def ies_property(self, short_name: str):
        short_name.replace("ies:", "")  # just in case someone used the prefix

        if self.ies_uri_stub + short_name not in self.properties:
            logger.warning(f"property {short_name} not in IES ontology")

        return f"{self.ies_uri_stub}{short_name}"
