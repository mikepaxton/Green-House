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
from Adafruit_IO import Client
import os
import Adafruit_DHT
from Subfact_ina219 import INA219
import logging


#  Initialize DHT sensor and define the RPi pin number.
DHT_TYPE = Adafruit_DHT.DHT22
DHT_PIN  = 23  # RPi pin number

# Initialize Adafruit IO.  Use the key that has been assigned to you on io.adafruit.com.
ADAFRUIT_IO_KEY = 'your key goes here.'
aio = Client(ADAFRUIT_IO_KEY)

# Setup configs
#date = datetime.now()

# Main definitions
def getCPUtemp():
    """Function used to grab RPi CPU Temp and return CPU temperature as a character
    string"""
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

def cels_fahr(cels):
    """Function takes in celsius temperature and returns temp in Fahrenheit"""
    temp = cels * 9.0 / 5 + 32
    return(temp)

def getDHT():
    """ Attempt to get sensor reading of DHT.  If it is unable to it will continue
    trying until it succeeds. This can happen if the CPU is under a lot of load and
    the sensor can't be reliably read (timing is critical to read the sensor).
    Temp is converted to Fahrenheit.
    """
    while True:
        humidity, cels = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
        if cels and humidity:
            dht_temp = cels_fahr(cels)
        else:
            continue

def getSolar():
    """ Gather INA219 sensor readings for Solar Panels.
    The addresses for the INA219 are: ['0x40', '0x41', '0x44']
    """
    for i2caddr in ['0x40']:
        ina = INA219(address=int(i2caddr,16))
        sol_bus_v = ina.getBusVoltage_V()
        sol_shunt_mv = ina.getShuntVoltage_mV()
        sol_curr_ma = ina.getCurrent_mA()
        sol_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000 )

def getBat():
    """ Gather INA219 sensor readings for Battery"""
    for i2caddr in ['0x41']:
        ina = INA219(address=int(i2caddr,16))
        bat_bus_v = ina.getBusVoltage_V()
        bat_shunt_mv = ina.getShuntVoltage_mV()
        bat_curr_ma = ina.getCurrent_mA()
        bat_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000 )


""" Main Loop """

while True:

    try:
        """ Get CPU temp and send it to aio.  There should be no errors so except just
        passes.
        """
        getCPUtemp()
        cels = float(getCPUtemperature())
        cpu_temp = cels_fahr(cels)
        aio.send('greenhouse-cpu-temp', cpu_temp)
    except:
        pass


    try:
        """ Grab DHT's temp and humidity. Function continues to try getting readings
        so except passes.
        """
        getDHT()
        aio.send('greenhouse-temperature', dht_temp)
        aio.send('greenhouse-humidity', humidity)
    except:
        pass

    try:
        """ Get solar panel voltage and current.
        """
        getBat()
        aio.send('greenhouse-sol-volt', sol_volt_v)
        aio.send('greenhouse-sol-current', sol_curr_ma)
    except:
        pass

    try:
        """ Get battery voltage and current.
        """
        getBat()
        aio.send('greenhouse-bat-volt', bat_volt_v)
        aio.send('greenhouse-bat-current', bat_curr_ma)
    except:
        pass

