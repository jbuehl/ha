Buehltech Home Automation
=========================

Terminology
-----------
Here is a definition of the terminology used in this project.

##### PHYSICAL
- sensor - a device that has a state that can be read
- control - a device whose state can be read and also changed
- server - a device that may be connected to one or more sensors and communicates with one or more servers
- client - a device that presents a user interface and communicates with one or more servers
- interface - the connection over which two devices communicate

##### MODEL
- resource - the fundamental object
- sensor - a representation of a physical sensor
- control - a representation of a physical control
- interface - a representation of a physical interface
- collection - an ordered list of resources
- task - a specification of a control, a state, and a time 
- schedule - a collection of tasks

##### DEPLOYMENT
- application - the implementation of a collection of resources and interfaces that runs on a server
- service - an application that implements the server side of an interface to a client device or server device
- client - an application that implements the client side of an interface to a server device

Naming
------
Every resource has a system-wide unique identifier.

States
------
Every resource has an associated state.

Object model
------------
HA uses an object model that is defined by the following classes:

	+ class HAResource(object):
	    - class HAInterface(HAResource):
	    + class HASensor(HAResource):
	            - class HAView(object):
	        + class HAControl(HASensor):
	            - class HACycle(object):
	            - class HASequence(HAControl):
	            - class HAScene(HAControl):
	    + class HACollection(HAResource, OrderedDict):
	        + class HASchedule(HACollection):
	            + class HATask(HAControl):
	                + class HASchedTime(object):

##### HAResource
The base class for most HA objects.

    - name
        
##### HAInterface
Defines the abstract class for interface implementations.

    - interface
    - sensors
    - start()
    - stop()
    - read(addr)
    - write(addr, value)
    - notify()
    - getStateType(HASensor)
        
##### HASensor
Defines the model for the basic HA sensor.

    - interface
    - addr
    - type
    - label
    - group
    - view
    - location
    - notify()
    - getState()
    - getStateChange()
    - getStateType()
        
##### HAControl
Defines the model for a sensor whose state can be changed.

    - setState(value)

##### HACycle, HASequence, and HAScene
Used to define aggregations of HAControls that 
can be set collectively.

##### HACollection
Defines an ordered list of HAResources.

##### HASchedule, HATask, and HASchedTime
Used to manage a list of tasks to be run at 
specified times.
        
Implementation
--------------

The HA object model is defined in ha/HAClasses.py.

Interfaces to specific hardware are implemented in ha/*Interface.py.

Runtime parameters are defined in ha/HAConf.py.

Programs that run on servers are defined in ha*.py.
The systemd service definitions are defined in ha*.service.
  
    - haLights.py	
    - haShades.py	
    - haSprinklers.py
    - haPool.py	
    - haSolar.py
    - haLoads.py
    	
A service that aggregates all the servers and provides a web interface is implemented in 
haWeb.py.

Services expose their HA objects in a REST interface that is implemented in 
ha/restServer.py.

Access
------
The HA REST interface allows access to HA objects.

##### Resource paths 
Paths are defined by the organization of collections that the implementing program 
has  passed to the REST server.  A path consists of one of more HACollection names, 
optionally  followed by a HASensor name, optionally followed by an HASensor 
attribute name.

The HASensor attribute "state" returns the current state of the sensor.  The
attribute "stateChange" waits and returns the state of a sensor when the state
changes.

Each REST server includes a resource named "states" whose "state" attribute
consists of a dictionary of all the states of the HASensors in the collection.  It
also has an attribute called "stateChange" that waits for at least one of the resource
states to change and returns the states of all the resources.

##### Verbs
The following verbs are defined:
- GET - return the value of the specified resource
- PUT - set the specified resource attribute to the specified value
- POST - not implemented
- DELETE - not implemented

##### Data
Data that is returned from a GET or specified in the body of a PUT is the JSON 
representation of the specified resource.

##### Advertising
The HA REST server sends a periodic message to port 4242 on the broadcast address of 
the local network to advertise itself.  The message contains the hostname, port, 
and resource collection that is served.
    
##### Examples
    1. Return the list of resources on the specified server.

        GET hostname:7378/resources

        {"type": "collection", "class": "HACollection", "resources": ["Null", 
        "frontLawn", "backLawn", "backBeds", "sideBeds", "gardenSequence", 
        "backLawnSequence", "sideBedSequence", "gardenTask", "backLawnTask", 
        "sideBedTask", "inverterTemp", "currentPower", "todaysEnergy", "lifetimeEnergy", 
        "lightsLoad", "plugsLoad", "appl1Load", "appl2Load", "cookingLoad", "acLoad", 
        "poolLoad", "backLoad", "xmasLights", "frontLights", "backLights", "bbqLights", 
        "backYardLights", "outsideLights", "recircPump", "Outside lights on sunset", 
        "Outside lights off midnight", "Outside lights off sunrise", 
        "Hot water recirc on", "Hot water recirc off", "Outside lights on sunset event", 
        "Outside lights off sunrise event", "shade1", "shade2", "shade3", "shade4", 
        "allShades", "Shades down", "Shades up Jun, Jul", "Shades up May, Aug", 
        "Shades up Sep", "poolLight", "spaLight", "poolLights", "outsideAirTemp", 
        "poolTemp", "spaTemp", "poolPump", "poolPumpSpeed", "poolPumpFlow", 
        "poolCleaner", "spa", "spaHeater", "spaBlower", "model", "date", "time", 
        "cleanMode", "spaWarmup", "spaReady", "spaShutdown", "poolPumpPower", 
        "poolCleanerPower", "spaBlowerPower", "poolLightPower", "spaLightPower", 
        "Pool cleaning"], "name": "resources"}

    2. Return the attributes for the resource "shade1".  Note that the attributes 
       "state" or "stateChange" are not included.

        GET hostname:7378/resources/shade1

        {"addr": "/resources/sensors/shade1/state", "group": "Doors", "name": "shade1", 
        "location": null, "interface": "rpi04:7378", "type": "shade", "class": 
        "HAControl", "label": "Shade 1"}
     
    3. Return the current state of the resource "shade1".

        GET hostname:7378/resources/shade1/state

        {"state": 0}

    4. Set the state of the resource "shade1" to 1.

        PUT hostname:7378/resources/shade1/state

        {"state": 1}
     
    5. Return the state of the resource "lightsLoad" when the state changes.  This will
       block and wait indefinitely until the state changes.

        GET hostname:7378/resources/lightsLoad/stateChange

        {"stateChange": 27.48}

    6. Return the current states of all resources on the specified host.

        GET hostname:7378/resources/states/state

        {"state": {"acLoad": 0.0, "cookingLoad": 0.0, "poolLoad": 50.879999999999995, 
        "backLoad": 985.2, "plugsLoad": 278.4, "appl1Load": 24.0, "lightsLoad": 27.6, 
        "appl2Load": 20.520000000000003}}

    7. Return the state of the current states of all resources on the specified host 
       when a state changes.  This will block and wait indefinitely until at least one 
       state changes.

        GET hostname:7378/resources/states/stateChange

        {"stateChange": {"backLoad": 980.8799999999999, "poolLoad": 59.28}}


