# Buehltech Home Automation REST interface

### Overview
HA applications can expose their HA resources via an interface that is implemented in
ha/rest/restServer.py. This allows a client application to access
HA objects on other servers.

### Requirements
* enables distributability
* client-server model
* autodiscovery of LAN services
* stateless servers
* transport level security

### Terminology
* server - hardware that is running one or more HA applications
* hostname - the unique name for a server on the local network
* HA service - the implementation of the HA REST interface on a server
* HA resource - a HA object implemented within a HA application
* REST resource - an identifier in a the HTTP path that may describe a HA resource

### Service advertising
The HA REST server uses periodic messages sent to a multicast address to advertise itself on the local network.  
The message contains the service name, and port that a client can use to contact it.  The default port is 7378.  
If multiple HA services are running on the same host they must use different ports.

The message contains a service REST resource and optionally a resources REST resource and states REST resource.
If the message only contains a service REST resource, the message serves to notify clients that the server is
still active and there haven't been any resource or state changes since the last message.  The timestamp will be the
same as the previous message and the sequence number will be incremented by 1.

A client will create local resources that serve as proxies for the resources on a server.  The states of the resources
are cached in the client and updated when the states of the server resources change.  When a client receives a message
for a service that it hasn't previously seen, it creates a set of proxy resources for the service.

If the state of a resource changes on a server, the next message will include a states REST resource that contains
the current states of all resources on the server and an updated timestamp.  The client should update it's state cache
for that service with the new values.

If the configuration of the HA resources on a service changes, the next message will include both a resources REST resource,
a states REST resource, and an updated timestamp.  The client will delete and recreate the proxied HA resources for
that service, and update their states.

If a client receives a message from an active server that contains a changed timestamp but no resources or states REST resources,
it will request those resources from the service and update its cache.

### Verbs
The HTTP following verbs are implemented by restServer.py:
- GET - return the value of the specified HA resource
- PUT - set the specified HA resource attribute to the specified value
- POST - create a new HA resource (not implemented)
- DELETE - delete the specified HA resource (not implemented)

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
"service":  {"name": <service name>,
			 "hostname": <host name>,
			 "port": <port>,
			 "label": <service display name>,
			 "timestamp": <last update time of the resource states>,
			 "seq": <sequence number of the message>}
```
The /resources/ REST resource contains a JSON representation of the HA resource that
the service is exposing.  It may be a single HA Resource but typically this is a
HA Collection resource that contains a list of HA resources.
```
"resources":{"class": "Collection",
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
If an attribute references another resource, the value contains only the name of the referenced resource,
not the JSON representation of that resource.  If an attribute references a class that is not a resource,
the JSON representation of the object is the value of the attribute.
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
Examples 1-5 show messages that are used for discovery of the configuration of resources.  Examples 6-7 show
messages that get the current state of resources.  Example 8 shows changing the state of a resource.  Example 9
shows the notification of state changes of resources.

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

7. Return the current states of all resources on the host sprinklers.local.

       Request:     GET sprinklers.local:7378/states

       Response:    {"states": {"gardenTemp": 28.0,
                                "gardenSprinkler": 0}}

8. Set the state of the resource "gardenSprinkler" to 1.  The request body contains
	   the requested state.  The response body returns the resulting state.

       Request:     PUT sprinklers.local:7378/resources/gardenSprinkler/state
                    {"state": 1}

       Response:    {"state": 1}

9. Unsolicited message that is broadcast periodically and whenever one of the states changes
	   that shows the current states of all resources in the service sprinklerService.

       Message:     {"service": {"name": "sprinklerService",
                                 "label": "Sprinklers",
                                 "timestamp": 1595529456,
                                 "seq": 667},
                     "states": {"gardenTemp": 28.0,
                                "gardenSprinkler": 0}}
