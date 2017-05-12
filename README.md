Table of Contents
===
 0. Foreword
 1. Synopsis
 2. Latest Version
 3. Installation
 4. Documentation
 5. Bug Reporting
 6. Contributors
 7. Contacts
 8. License
 9. Copyright

0. Foreword
===
As OBNL uses AMQP/MQTT protocol (with pika), a server SHALL be running. If docker is 
installed the following command starts a RabbitMQ server:  
    docker run -d --hostname my-rabbit -p 5672:5672 --name some-rabbit rabbitmq:alpine

1. Synopsis
===
OBNL was firstly imagine as a light implementation of OpenBuildNet (OBN) in Python.
Its name initially means OpenBuildNet Light.

The main purpose of OBNL is simulator communication to simply realise a co-simulation.

During the first development and tests, we realise that it was very complicated
to match the requirement of OBN. Therefore we decide to realise a co-simulator based on
OBN - an "OpenBuildNet Like" co-simulator.

2. Latest Version
===
You can find the latest version of OBNL on :
    https://github.com/ppuertocrem/obnl


3. Installation
===
OBNL is a full python project thus as long as Python is installed on your
system you can install it by moving in the root folder (the folder this README
file should be) and run :

    python setup.py install
    
In some systems you need Administrator right to run this command.

Warning : OBNL requires these packages to be used in full :

 * pika
 * protobuf


4. Documentation
===
Currently, the documentation is only accessible in source code.


5. Bug Reporting
===
If you find any bugs, or if you want new features you can put your request on
github at the following address :
    https://github.com/ppuertocrem/obnl


6. Contributors
===

The OBNL Team is currently composed of :

 * Pablo Puerto (pablo.puerto@crem.ch)
 * Gillian Basso (gillian.basso@hevs.ch)
 * Jessen Page (jessen.page@hevs.ch)


7. Contacts
===
For questions, bug reports, patches and new elements / modules, please use the Bug Reporting.


8. License
===
You should have received a copy of the GNU General Public License along with
this program.
If not, see <http://www.gnu.org/licenses/>.


9. Copyright
===
Copyright (C) 2011-2017 The OBNL Team

This file is part of the OBNL project.

The OBNL project is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation; either version 3 of the License, or (at your option) any
later version.

The OBNL project is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
