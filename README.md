# Buehltech Home Automation

This project implements a system that enables sensing and control of various devices in a home.

### Overview

Any device in the home that can be controlled electronically can be connected to a system that can manage that device and allow remote access. Examples of devices include such things as light fixtures, sprinkler valves, temperature sensors, door sensors, etc.  This project does not define specific hardware for these devices, but rather defines the software that allows any device to be interfaced to the system.

At the lowest level, a template is defined that allows a hardware interface to be abstracted to a common API.  The server on which the software is running may physically connect to the device using any hardware interface such as GPIO pins, a serial port, or a network adapter.  An object model is defined that is implemented with an application running on that server that further abstracts the specific functions of the device.  Network protocols are defined that enable the server to advertise itself on the network and allow access to the devices that it is connected to. Other servers may implement human interfaces such as a web server.

### Example

A very simple example is a temperature sensor that may be in a room, outside the house, or immersed in a swimming pool.  All it does is to report the ambient temperature of the air or water it is in.  Let's consider a digital temperature sensor that uses the I2C hardware interface.  When a read command is sent to the address of the device it returns a byte that represents the temperature in degrees Celsius.  Two software objects defined by this project are required - a Sensor and an Interface.  The Sensor can be just the basic object because all it needs to do is to implement the getState() function that reads the state of the sensor from the interface it is associated with.  The Interface object must be specific to the I2C interface so it is a I2cInterface object that is derived from the basic object.  It can use the Python smbus library that performs all the low level I2C protocol functions to read a byte and implement the read() function.

Another example is a sprinkler valve.  The state of the valve is either open or closed, and it is operated remotely from the network.  The voltage to the valve  is switched using a relay or semiconductor that is controlled by a GPIO pin on the controller.

### Design goals

The design of the project targets the following goals.  Not all of them have been strictly met.

- Distributed
- Devices are discoverable
- Connected to the network
- Not dependent on the internet for critical functions
- Secure
- Not dependent on proprietary systems, interfaces, or devices
- Devices are autonomous if possible
- Not operating system specific

### Terminology

Here is a definition of the terminology used in this project.

##### PHYSICAL
- sensor - a device that has a state that can be read
- control - a device whose state can be read and also changed
- server - a device that may be connected to one or more sensors and communicates with one or more servers
- client - a device that presents a user interface and communicates with one or more servers
- interface - the connection over which two devices communicate

##### MODEL
- Resource - the fundamental object
- Sensor - a representation of a physical sensor
- Control - a representation of a physical control
- Interface - a representation of a physical interface
- Collection - an ordered list of resources
- Task - a specification of a control, a state, and a time
- Schedule - a collection of tasks

##### DEPLOYMENT
- application - the implementation of a collection of resources and interfaces that runs on a server
- service - an application that implements the server side of an interface to a client device or server device
- client - an application that implements the client side of an interface to a server device

### Naming

Every resource has a system-wide unique identifier.  The namespace is flat.

### States

Every resource has an associated state.  A resource state is a single scalar number or string.  If a device has multiple attributes or controls, it should be represented as multiple sensors or controls.

### Object model

Home automation uses an object model that is defined by the following base classes:

	+ class Resource(object):
	    - class Interface(Resource):
	    + class Sensor(Resource):
	        - class Control(Sensor):
	    + class Collection(Resource, OrderedDict):
	        + class Schedule(Collection):
	            - class Task(Control):

Other classes are inherited from the base classes:

    - class Sequence(Control):
    - class SensorGroup(Sensor):
    - class ControlGroup(SensorGroup, Control):
    - class CalcSensor(Sensor):
    - class ResourceStateSensor(Sensor):

These standalone classes are used by the HA classes

    - class Cycle(object):
    - class SchedTime(object):

##### Resource
The base class for most HA objects.

    - name

##### Interface
Defines the abstract class for interface implementations.

    - interface
    - sensors
    - event
    - start()
    - stop()
    - read(addr)
    - write(addr, value)
    - notify()
    - getStateType(Sensor)

##### Sensor
Defines the model for the basic HA sensor.

    - interface
    - addr
    - event
    - type
    - label
    - group
    - view
    - location
    - notify()
    - getState()
    - getStateChange()
    - getStateType()

##### Control
Defines the model for a sensor whose state can be changed.

    - setState(value)

##### Cycle, Sequence, SensorGroup, and ControlGroup
Used to define aggregations of Sensors that
can be managed collectively.

##### Collection
Defines an ordered list of Resources.

##### Schedule, Task, and SchedTime
Used to manage a list of tasks to be run at
specified times.

### Implementation

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
ha.rest.restServer.py.

### Access

The HA REST interface allows access to HA objects.

##### Resource paths
Paths are defined by the organization of collections that the implementing program
has  passed to the REST server.  A path consists of one of more Collection names,
optionally  followed by a Sensor name, optionally followed by an Sensor
attribute name.

The Sensor attribute "state" returns the current state of the sensor.  The
attribute "stateChange" waits and returns the state of a sensor when the state
changes.

Each REST service resource collection includes an extra resource named "states" whose "state" attribute
consists of a dictionary of all the current states of the Sensors in the collection.  It
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

        {"type": "collection", "class": "Collection", "resources": ["Null",
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
        "Control", "label": "Shade 1"}

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
