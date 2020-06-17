# Buehltech Home Automation

### Overview

This project implements a system that enables sensing and control of various devices in a home.

Any device in the home that can be sensed or controlled electronically can be connected to a system that can manage that device and allow remote access. Examples of devices include such things as light fixtures, sprinkler valves, temperature sensors, door sensors, etc.  This project does not define specific hardware for these devices, but rather defines the software that allows any device to be interfaced to the system.

At the lowest level, a template is defined that allows a hardware interface to be abstracted to a common API.  The server on which the software is running may physically connect to the device using any hardware interface such as GPIO pins, a serial port, or a network adapter.  An object model is defined that is implemented with an application running on that server that further abstracts the specific functions of the device.  Network protocols are defined that enable the server to advertise itself on the network and allow access to the devices that it is connected to. Other servers may implement human interfaces such as a web server.

### Example

A simple example is a temperature sensor that may be in a room, outside the house, or immersed in a swimming pool.  All it does is to report the ambient temperature of the air or water it is in.  Let's consider a digital temperature sensor that uses the I2C hardware interface.  When a read command is sent to the address of the device it returns a byte that represents the temperature in degrees Celsius.  Two software objects defined by this project are required: a Sensor and an Interface.  The Sensor can be just the basic object because all it needs to do is to implement the getState() function that reads the state of the sensor from the interface it is associated with.  The Interface object must be specific to the I2C interface so it is a I2cInterface object that is derived from the basic object.  It can use the Python SMBus library that performs all the low level I2C protocol functions to read a byte and implement the read() function.

Another example is a sprinkler valve.  The state of the valve is either open or closed, and it is operated remotely from the network.  The voltage to the valve is switched using a relay or semiconductor that is controlled by a GPIO pin on the controller.  A Control object and an Interface object are needed to implement this.  The Control object inherits the getState() function from the Sensor object, but it also defines a setState() function that changes the state of the device.  The GPIOInterface object implements the read() and write() functions that get and set a GPIO pin.

### Design goals

The design of the project targets the following goals.  Not all of them have been strictly met.

##### Distributed
Functions are distributed across devices in the system.

##### Devices are autonomous
Whenever possible, devices can run independently of the system.  There is no requirement for a centralized controller.

##### Devices are dynamically discoverable
Devices can be added or removed from the system without requiring changes to a system configuration.

##### Connected to the local home network
Devices are connected to the system via the local wired or wireless home network.

##### Not dependent on the internet for critical functions
The system may be accessed remotely via the internet and use cloud servers for certain functions, however internet connectivity is not required.

##### Reasonably secure
The system does not explicitly implement any security features.  It relies on the security of the local network.

##### Not dependent on proprietary systems, interfaces, or devices
Proprietary interfaces and devices may be accessed, but there is no requirement for any particular manufacturer's products.

##### Not operating system specific
There is no dependence on any operating system specific features.

##### Open source
All code is open source.

### Terminology

Here is a definition of the terminology used in this project.

##### PHYSICAL
- sensor - a device that has a state that can be read
- control - a device whose state can be read and also changed
- server - a device that may be connected to one or more sensors and communicates with one or more clients
- client - a device that communicates with one or more servers
- interface - the connection over which two devices communicate

##### OBJECT MODEL
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

The object model is defined by the following basic classes:

	+ class Resource(object):
	    - class Interface(Resource):
	    + class Sensor(Resource):
	        - class Control(Sensor):
	    + class Collection(Resource, OrderedDict):

Other generally useful classes are inherited from the basic classes:

	+ class SensorGroup(Sensor):
		- class ControlGroup(SensorGroup, Control):
	- class CalcSensor(Sensor):
	- class ResourceStateSensor(Sensor):
	- class DependentControl(Control):
	- class MomentaryControl(Control):
	- class MultiControl(Control):
	- class MinMaxControl(Control):
	- class MinSensor(Sensor):
	- class MaxSensor(Sensor):
	- class AccumSensor(Sensor):
	- class AttributeSensor(Sensor):

These classes are inherited from the basic classes and implement time based functions:

	- class Schedule(Collection):
    - class Cycle(object):
	- class Sequence(Control):
	- class Task(Control):
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
    - location
    - notify()
    - getState()
    - getStateChange()
    - getStateType()

##### Control
Defines the model for a sensor whose state can be changed.

    - setState(value)

##### SensorGroup, and ControlGroup
Used to define aggregations of Sensors that
can be managed collectively.

##### Collection
Defines an ordered list of Resources.

##### Schedule, Cycle, Sequence, Task, and SchedTime
Used to manage a list of tasks to be run at
specified times.

### Sample application

The following sample application illustrates how a service may be implemented.  A temperature sensor and a sprinkler valve are configured as described in the earlier example.

First, the I2C and GPIO Interface objects are defined.  The address of the temperature sensor is 0x4b on the I2C bus and the sprinkler valve is connected to GPIO pin 17 which is set to output mode.  Then the Sensor for the temperature and the Control for the sprinkler valve are defined.  Next, a Task is defined that will run the sprinkler every day at 6PM (18:00) for 10 minutes (600 seconds) every day during the months May through October.

Finally, the task is added to a Schedule object and the Sensor and Control are added to a Collection object that will be exported by the REST server.  When the Schedule is started it will turn on the sprinkler every day as programmed.  The REST server will export the representations of the two resources and their current states.  It will also allow another server to control the sprinkler valve remotely. It must be started last because it will block the application so it will not exit.

```
from ha import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.gpioInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
	# Interfaces
	i2cInterface = I2CInterface("i2cInterface")
	gpioInterface = GPIOInterface("gpioInterface", output=[17])

	# Temp sensor and sprinkler control
	gardenTemp = Sensor("gardenTemp", i2cInterface, 0x4b, label="Garden temperature")
	gardenSprinkler = Control("gardenSprinkler", gpioInterface, 17, label="Garden sprinkler")

	# Sprinkler task
	gardenTask = Task("gardenTask", SchedTime(hour=18, minute=00, month=[May, Jun, Jul, Aug, Sep, Oct]),
	                    sequence=Sequence("gardenSequence",
								cycleList=[Cycle(control=gardenSprinkler, duration=600, startState=1)]),
								controlState=1,
						label="Garden sprinkler task")

	# Resources and schedule
	schedule = Schedule("schedule", tasks=[gardenTask])
	restServer = RestServer("garden", Collection("resources",
				resources=[gardenTemp, gardenSprinkler]), label="Garden")

	# Start things up
	schedule.start()
	restServer.start()
```
### Implementation

#### Directory structure
```
root directory/
	*App.py - Applications that run on servers
	ha/
		basic.py - The basic object model
		extra.py - Additional useful objects derived from the basic objects
		environment.py - Environment variables
		config.py - Read runtime parameters from the configuration file
		logging.py - Logging functions
		debugging.py - Debugging functions
		schedule.py - Schedule and time based objects
		interfaces/
			*Interface.py - Interfaces to specific hardware
		rest/
			restConfig.py - REST interface parameters
			restServer.py - REST server used by a service
			restProxy.py - REST proxy used by a client
			restServiceProxy.py - The proxy for a REST service used by a client
			restInterface.py - The interface used by resources that are being proxied in a client
		ui/
			webUi.py - A human interface that aggregates all the servers and provides a web interface
			webViews.py
		services/
			*App.service - The systemd service definitions
```
### Access
Services expose their HA objects in a REST interface that is implemented in
ha/rest/restServer.py. The RestInterface object allows a client application to access HA objects on other servers.

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
The HTTP following verbs are implemented by restServer.py:
- GET - return the value of the specified resource
- PUT - set the specified resource attribute to the specified value
- POST - not implemented
- DELETE - not implemented

##### Data
If an HTTP request is sent to port 7378 on a host that is running the REST server the data that is returned from a GET or specified in the body of a PUT is the JSON
representation of the specified resource.

##### Service advertising
The HA REST server sends a periodic message to port 4242 on either the IPV4 broadcast address of
the local network or a multicast group to advertise itself.  The message contains the hostname, port,
and resource collection that is served.

##### State notifications
The HA REST server sends a periodic message to port 4243 on either the IPV4 broadcast address of
the local network or a multicast group to advertise the current state of its resources.  This is usually sent
when the state of the resource changes.  The message contains the
JSON representation of the state of the resource.

##### Examples
    1. Return the list of resources on the specified server.

        GET hostname:7378/resources

        {"type": "collection", "class": "Collection", "resources": ["gardenTemp", "gardenSprinkler"], "name": "resources"}

    2. Return the attributes for the resource "gardenSprinkler".  Note that the attributes
       "state" or "stateChange" are not included.

        GET hostname:7378/resources/gardenSprinkler

        {"addr": 17, "group": "", "name": "gardenSprinkler",
        "location": null, "type": "", "class":
        "Control", "label": "Garden sprinkler"}

    3. Return the current state of the resource "gardenSprinkler".

        GET hostname:7378/resources/gardenSprinkler/state

        {"state": 0}

    4. Set the state of the resource "gardenSprinkler" to 1.

        PUT hostname:7378/resources/gardenSprinkler/state

        {"state": 1}

    5. Return the state of the resource "gardenTemp" when the state changes.  This will
       block and wait indefinitely until the state changes.

        GET hostname:7378/resources/gardenTemp/stateChange

        {"stateChange": 27.48}

    6. Return the current states of all resources on the specified host.

        GET hostname:7378/resources/states/state

        {"state": {"gardenTemp": 28.0, "gardenSprinkler": 0}}

    7. Return the state of the current states of all resources on the specified host
       when a state changes.  This will block and wait indefinitely until at least one
       state changes.

        GET hostname:7378/resources/states/stateChange

        {"stateChange": {"gardenTemp": 28.0, "gardenSprinkler": 1}}
