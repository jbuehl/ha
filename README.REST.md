# Buehltech Home Automation REST interface

### Overview
HA applications can expose their HA resources in a REST interface that is implemented in
ha/rest/restServer.py in the RestServer object. This allows a client application to access
HA objects on other servers.

### Terminology

* server - hardware that is running one or more HA applications
* hostname - the unique name for a server on the local network
* HA service - the implementation of the HA REST interface on a server
* HA resource - a HA object implemented within a HA application
* REST resource - an identifier in a the HTTP path that corresponds to a HA resource

### Service advertising
The HA REST server uses Zeroconf to advertise itself on the local network.  The message contains the service type, port,
and protocol that a client can use to contact it.  The default port is 7378.  If multiple HA services are running on the
same host they will use different ports.

* service type: ha-rest
* protocol: tcp
* hostname: <hostname>
* IP address: <ip address>
* port: <port>

### Verbs
The HTTP following verbs are implemented by restServer.py:
- GET - return the value of the specified HA resource
- PUT - set the specified HA resource attribute to the specified value
- POST - not implemented
- DELETE - not implemented

### Resource paths
REST resource paths are defined as follows:
```
/
	service/
		service attributes
	resources/
		resource 0/
			resource 0 attributes
		resource 1/
			resource 1 attributes
		...
		resource n/
			resource n attributes
	states/
		resource 0 state/
		resource 1 state/
		...
		resource n state/
```
The /service/ resource contains attributes of the HA service.
```
{"name": <service name>,
 "label": <service display name>,
 "timestamp": <last update time of the resource states>,
 "seq": <sequence number of the state update>}
```
The /resources/ REST resource contains a JSON representation of the HA resource that
the service is exposing.  It may be a single HA Resource but typically this is a
HA Collection resource that contains a list of HA resource names.
```
{"class": "Collection",
 "attrs": {"name": <resource collection name>,
           "type": "collection",
           "resources": [<resource 0 name>,
                         <resource 1 name>,
                         ...,
                         <resource N name>]}}
```

The /states/ resource contains a list of all the names and current states of the HA Sensor
resources in the service.
```
{"states": {<resource 0 name>: <resource 0 state>,
            <resource 1 name>: <resource 1 state>,
            ...,
            <resource N name>: <resource N state>}}
```

### Resource attributes
If an HTTP request is sent to port 7378 on a host that is running the REST server the data that is
returned from a GET is the JSON representation of the specified HA resource.
Every HA Sensor resource has an implied attribute "state" that returns the current state of the sensor. It
is not included in the list of attributes returned for the resource, however it may be queried
in the same way as any other resource attribute.
```
{"class": <class name>,
 "attrs": {<attr 0>: <value 0>,
           <attr 1>: <value 1>,
           ...,
           <attr N>: <value N>}}
```

### State notifications
In addition to implementing the REST interface for client queries,
an HA REST server may send an unsolicited message to port 4243 on either the IPV4 broadcast address of
the local network or a multicast group to advertise the current state of its HA resources.  This is usually sent
when the state of a resource changes and may be sent periodically to indicate that the service is active.  
The message contains the JSON representation of the service
name and the current state of the HA resources published by that service.
```
{"service": {"name": <service name>},
 "states": {<resource 0 name>: <resource 0 state>,
            <resource 1 name>: <resource 1 state>,
            ...,
            <resource N name>: <resource N state>}}
```

### Examples
1. Return the list of resources on the host sprinklers.local.

	   Request:     GET sprinklers.local:7378

	   Response:    ["service",
                     "resources",
                     "states"]

2. Return the attributes of the HA service on the host sprinklers.local.

	   Request:     GET sprinklers.local:7378/service

	   Response:    {"name": "sprinklerService",
                     "label": "Sprinklers",
                     "timestamp": 1595529166,
                     "seq": 666}

3. Return the list of HA resources on the host sprinklers.local.

       Request:     GET sprinklers.local:7378/resources

       Response:    {"class": "Collection",
                     "attrs": {"name": "resources",
                               "type": "collection",
                               "resources": ["gardenTemp",
                                             "gardenSprinkler"]}}

4. Return the attributes for the resource "gardenSprinkler".  Note that the attribute
       "state" is not included.

       Request:     GET sprinklers.local:7378/resources/gardenSprinkler

	   Response:    {"class": "Control",
                     "attrs": {"name": "gardenSprinkler",
                               "interface": "sprinklerInterface"
                               "addr": 17,
                               "location": null,
                               "type": "sprinkler",
                               "group": "Sprinklers",
                               "label": "Garden sprinkler"}}

5. Return the value of the attribute "addr" of the resource "gardenSprinkler".

	   Request:     GET sprinklers.local:7378/resources/gardenSprinkler/addr

	   Response:    {"addr": 17}

6. Return the current state of the resource "gardenSprinkler".

       Request:     GET sprinklers.local:7378/resources/gardenSprinkler/state

       Response:    {"state": 0}

7. Set the state of the resource "gardenSprinkler" to 1.  The request body contains
	   the requested state.  The response body returns the resulting state.

       Request:     PUT sprinklers.local:7378/resources/gardenSprinkler/state
                    {"state": 1}

       Response:    {"state": 1}

8. Return the current states of all resources on the specified host.

       Request:     GET sprinklers.local:7378/states

       Response:    {"states": {"gardenTemp": 28.0,
                                "gardenSprinkler": 0}}

9. Unsolicited message that is broadcast periodically and whenever one of the states changes
	   that shows the current states of all resources in the service sprinklerService.

       Message:     {"service": {"name": "sprinklerService"},
                                 "label": "Sprinklers",
                                 "timestamp": 1595529456,
                                 "seq": 667}
                     "states": {"gardenTemp": 28.0,
                                "gardenSprinkler": 0}}
