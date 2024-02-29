# telicent-ies-tool

A library for working with the [IES data standard.](https://github.com/dstl/IES4)

IES is a UK Government data exchange standard. It is a 4D ontology specified as an RDF Schema. The purpose of 
telicent-ies-tool is to make it easier for users to create compliant IES data.



## Dependencies

Python >= 3.8



## Install

```shell
pip install https://github.com/telicent-oss/ies-tool.git
```


## Usage

To import, use:

```python
from ies_tool.ies_tool import IESTool
```

To instantiate the tool:

```python
tool = IESTool(mode="rdflib")
```


### Namespaces

To bind a namespace uri stub to a prefix, we need to 'register' that namesapce. This needs to be done for all namespaces apart from: `xsd`, `dc`, `rdf`, `rdfs`, `owl` and `ies`.

```python
from ies_tool.ies_tool import IESTool, NamingScheme

tool = IESTool(mode="rdflib")
data_ns = NamingScheme(tool=tool, uri="http://example.com/rdf/testdata#")
data_ns.add_name("data", name_uri="http://example.com/rdf/testdata#__NAME")
tool.add_prefix("data", "http://example.com/rdf/testdata#")
```

As a default `http://example.com/rdf/testdata#` is used as a data uri stub. This can be changed: 

```python
tool.set_uri_stub('http://domain/rdf/stub#')
```


### Creating a Person
To create a person we need to instantiate a person object/class first. We can pass in several parameters, as shown below, as well as specify a unique uri or class, if needed.

```python
my_person = tool.create_person(
    given_name=given_name,
    family_name=family_name,
    dob=date_of_birth,
    pob=place_of_birth
)
```
We can then add additional information associated with the person using one of the available methods such as 
`add_identifier()`, `add_state()`, `in_location()`, `works_for()` etc.

#### Adding an identifier to a person
```python
my_person.add_identifier(person_id)
```


### Connecting nodes and edges
If no methods are available, we can create nodes using the  `instantiate()` method and connect this node to an existing node using the `add_to_graph()` method. 

```python
tool.add_to_graph(
    subjec=my_person.uri,
    predicate=f'{tool.ies_uri_stub}hasCharacteristic',
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

#### In a telicent-lib mapping function

```python
mapped_record = tool.graph.serialize(format="turtle") 
return mapped_record
```

#### Saving RDF locally

```python
tool.save_rdf("path/to/my/file.ttl",format="ttl")  
```
