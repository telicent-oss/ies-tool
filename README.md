# telicent-ies-tool

A library for working with the [IES data standard.](https://github.com/dstl/IES4)

IES is a UK Government data exchange standard. It is a 4D ontology specified as an RDF Schema. The purpose 
of telicent-ies-tool is to make it easier for users to create compliant IES data.

Formal ontologies can be hard for beginners to grasp. Unlike traditional data models, they are constructional
in nature. Instead of defining a set of entities and fields to populate, ontologies like IES define a set of
common objects that can be assembled following well-defined patterns. This introduces a degree of flexibility
not found in traditional data models, which is great for real-world situations where information requirements
change faster than the data models can be re-engineered. The disadvantage to this approach is that if users
and developers are not steeped in the principles that underpin the ontology (4D, extensional, constructional)
then it is easy to generate structures that do not follow the patterns. We can mitigate this somewhat with
the use of SHACL, but overuse of SHACL would result in the loss of desired flexibility.

To counter some of these issues, Telicent have collected together a number of convenience functions that we
have used on projects into one Python library to help data engineers get started and hopefully ensure 
appropriate use of the ontology. 



## Dependencies

Python >= 3.8



## Install

```shell
pip install telicent-ies-tool
```

## Overview & Approach

The IES Tool has a main factory class - `IESTool` - that takes care of storage, caching, and Python object instantiation.
It is necessary to initiate a tool object for every dataset you wish to work with.

```python
tool = IESTool()
```

As well as the main factory class, there are base Python classes for all the significant IES classes:

```
RdfsResource
    RdfsClass
    ExchangedItem
    Element
        Entity
        State
            EventParticipant
        Event

```

Each of these classes can be instantiated using typical Pythonic approach - e.g. 
```python
anne = Person(tool=tool, given_name="Anne", family_name="Smith")
```
Note that the initiation parameters must specify the IESTool instance you're using so it knows where to create the RDF
data. It is recommended that this approach is used in most cases. However, data can also be created using the `instantiate()` 
method on IESTool, the tool will attempt to determine the most appropriate Python base class to initiate - e.g.

```python
fred = tool.instantiate(classes=['http://ies.data.gov.uk/ontology/ies4#Person'])
```
The 'fred' object returned will be a Python Person object. It's generally better to just initiate the based classes though, as
it is not always possible to deterministically infer the Python class from the `instantiate()` call. Developers can override
the inference by setting the `base_class` parameter - e.g.


## Usage

To import, use:

```python
from ies_tool.ies_tool import IESTool
```

To instantiate the tool (factory) object:

```python
tool = IESTool()
```


### Namespaces

To bind an RDF namespace prefix, we need to 'register' that prefix. The library pre-configures prefixes: 
`xsd:`, `dc:`, `rdf:`, `rdfs:`, `owl:`, `ies:`, `iso8601:`, `iso3166:`

Registering these prefixes just enables shorter, more readable RDF to be produced. The methods in the IES tool itself all
require fully expanded URIs. 

```python
from ies_tool.ies_tool import IESTool, NamingScheme

tool = IESTool(mode="rdflib")

tool.add_prefix("data:", "http://example.com/rdf/testdata#")
```

As a default `http://example.com/rdf/testdata#` is used as a data uri stub. This can be changed: 

```python
tool.uri_stub = 'http://domain/rdf/stub#'
```
Note this will also set the blank prefix `:` to `http://domain/rdf/stub#`


### Creating a Person
To create a person we need to instantiate a person object/class first. We can pass in several parameters, as shown below, as well as specify a unique uri or class, if needed.

```python
my_person = Person(
    tool=tool,
    given_name='Fred',
    family_name='Smith',
    start="1985-08-21"
)
```
We can then add additional information associated with the person using one of the available methods such as 
`add_identifier()`, `add_state()`, `in_location()`, `works_for()` etc.


### Low-level operations (RDF / RDFS)
The base classes provide some simple methods for creating predicates:

```python
my_person.add_literal(predicate="http://xmlns.com/foaf/0.1/name",literal="Fred Smith")
my_person.add_label("SMITH, Fred")
my_person.add_comment("The one and only Fred Smith")
my_person.add_related_object(predicate="http://ies.data.gov.uk/ontology/ies4#ancestorOf",related_object=my_other_person)
```

The IES tool itself also provides a set of low-level methods for working with the graph, such as `add_to_graph` which adds an RDF statement:

```python
tool.add_to_graph(
    subject=my_person.uri,
    predicate='http://ies.data.gov.uk/ontology/ies4#hasCharacteristic',
    obj=characteristic_uri
)
```


### Labelling nodes in Telicent Graph

Primary names appear as node labels in Telicent Graph. 
To add a primary name to the person we have created earlier we can use the `"http://telicent.io/ontology/primaryName"` uri as a predicate and primary name as an object.

```python
tool.add_literal(
    subject=my_person.uri,
    predicate="http://telicent.io/ontology/primaryName",
    obj="my primary name string"
)
```

#### To clear the graph:

```python
tool.clear_graph()
```


### Saving/creating RDF

#### As a text string

```python
my_rdf_string = tool.get_rdf(format="turtle") 
```
As the IES tool uses RDFLib by default. If another storage plug-in has been used, it may not support all the RDF bindings.

#### Saving RDF locally

```python
tool.save_rdf("path/to/my/file.ttl",format="ttl")  
```
