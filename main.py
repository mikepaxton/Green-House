#!/user/bin/python2
""" This is my Green House Project which takes what I learned from my SolarPi
Project.  The purpose of this project is control the workings of my green house by
taking various sensor readings then using those readings to control the internal
temperature and humidity of the green house.
The sensors which will be used are the DHT22 for green house temp and humidity. The
INA219 for gathering the voltage and current input of the solar panels and the status
of the batteries.
The project will be using a Raspberry Pi for gathering the data and sending it out
using feeds to io.adafruit.com for charting.
Author:  Mike Paxton
Modification date: 02/13/16
"""

import datetime
