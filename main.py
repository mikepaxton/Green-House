#!/user/bin/python2
""" This is my Green House Project which takes what I've learned from my SolarPi
Project.  The purpose of this project is to control the workings of my green house by
taking various sensor readings then using those readings to control the internal
temperature and humidity of the green house.
The sensors which will be used are the DHT22 for green house temp and humidity. The
INA219 for gathering the voltage and current input of the solar panels and the status
of the batteries.
The project will be using a Raspberry Pi for gathering the data and sending it out
using feeds to io.adafruit.com for charting.
Author:  Mike Paxton
Modification date: 03/05/16
"""

import time
import datetime
from Adafruit_IO import Client
import Adafruit_DHT
from Subfact_ina219 import INA219
from TSL2561 import TSL2561
from ConfigParser import SafeConfigParser
import os
import MySQLdb

# TODO: Create a LCD control interface using tkinter or pygame
# TODO: Incorporate Python logging Module into controls
# TODO: Find a logging website other than io.adafruit for greater logging capabilities
# TODO: Work with the TSL2561 light sensor to check for data accuracy
# TODO: Make dbPort functional
# TODO: Incorporate two fans into code which should kick on when temp get to high


# Global stuff
config = SafeConfigParser()
config.read('config.cfg')
interval = config.get('defaults', 'interval')              # Get sensor updating interval
debug = config.getboolean('defaults', 'debug')             # debug print to console
ADAFRUIT_IO_KEY = config.get('defaults', 'aio_key')        # Import Adafruit aio Key
aio = Client(ADAFRUIT_IO_KEY)
DHT_TYPE = Adafruit_DHT.DHT22                              # Get DHT Pin number
DHT_PIN = config.get('defaults', 'dht_pin')
mysqlUpdate = config.getboolean('defaults', 'mysqlUpdate') # Check if using MySQL database
tsl = TSL2561()
temp_threshold = config.get('defaults', 'temp_threshold')
temp_norm = config.get('defaults', 'temp_norm')


def checkDebug(message):
    if debug == True:
        print(message)


# Debug config file information
checkDebug('Adafruit aio key: ' + str(ADAFRUIT_IO_KEY))
checkDebug('DHT pin used: ' + str(DHT_PIN))
checkDebug('Using Database: ' + str(mysqlUpdate))
checkDebug('Update interval in seconds: ' + str(interval))


def dbUpdate():
    """ Open a connection to mysql database using the MySQLdb library.  The database
    can be either local or remote.  If remote you must change both the dbaddress and
    the port number to that of remote. Changed the database connection information
    over to the config file.  Note: dbPort is not implemented in code yet.
    """
    dbAddress = config.get('defaults', 'dbAddress')
    dbUser = config.get('defaults', 'dbUser')
    dbPassword = config.get('defaults', 'dbPassword')
    dbName = config.get('defaults', 'dbName')
    #dbPort = config.get('defaults', 'dbPort')
    con = MySQLdb.connect(host=dbAddress, user=dbUser, passwd=dbPassword, db=dbName)
    c = con.cursor()

    date = datetime.datetime.now()
    c.execute("INSERT INTO sensor_data (date, dht_temp, dht_humidity, cpu_temp, "
              "solar_voltage, solar_current, battery_voltage, battery_current, lux, "
              "ir) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
              (date, dht_temp, humidity, cpu_temp, sol_volt_v, sol_curr_ma,
               bat_volt_v, bat_curr_ma, lux, ir))

    con.commit()
    con.close()


# Main Functions
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
    try:
        humidity, cels = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
        if cels and humidity:
            dht_temp = cels_fahr(cels)
        else:
            dht_temp = 0
            humidity = 0
            checkDebug('Unable to get DHT values!')
    finally:
        return dht_temp, humidity


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
    return sol_volt_v, sol_curr_ma


def getBat():
    """ Gather INA219 sensor readings for Battery"""
    for i2caddr in ['0x41']:
        ina = INA219(address=int(i2caddr,16))
        bat_bus_v = ina.getBusVoltage_V()
        bat_shunt_mv = ina.getShuntVoltage_mV()
        bat_curr_ma = ina.getCurrent_mA()
        bat_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000 )
    return bat_volt_v, bat_curr_ma


""" Main Loop"""
while True:

    try:
        """ Get CPU temp and send it to aio.  The value is set to two decimal places.
        """
        getCPUtemp()
        cels = float(getCPUtemp())
        cpu_temp = cels_fahr(cels)
        aio.send('greenhouse-cpu-temp', '{:.2f}'.format(cpu_temp))
    finally:
        checkDebug('CPU Temp: ' + str(cpu_temp))

    try:
        """ Grab DHT's temp and humidity. Function continues to try getting readings
        so except passes.  The value is set to two decimal places.
        """
        dht_temp, humidity = getDHT()
        aio.send('greenhouse-temperature', '{:.2f}'.format(dht_temp))
        aio.send('greenhouse-humidity', '{:.2f}'.format(humidity))
    finally:
        checkDebug('DHT Temp: ' + str(dht_temp))
        checkDebug('DHT Humidity: ' + str(humidity))

    try:
        """ Get solar panel voltage and current.  The value is set to two decimal places.
        """
        sol_volt_v, sol_curr_ma = getSolar()
        aio.send('greenhouse-sol-volt', '{:.2f}'.format(sol_volt_v))
        aio.send('greenhouse-sol-current', '{:.2f}'.format(sol_curr_ma))
    finally:
        checkDebug('Solar Panel volts: ' + str(sol_volt_v))
        checkDebug('Solar Panel current: ' + str(sol_curr_ma))

    try:
        """ Get battery voltage and current.  The value is set to two decimal places.
        """
        bat_volt_v, bat_curr_ma = getBat()
        aio.send('greenhouse-bat-volt', '{:.2f}'.format(bat_volt_v))
        aio.send('greenhouse-bat-current','{:.2f}'.format(bat_curr_ma))
    finally:
        checkDebug('Battery volts: ' + str(bat_volt_v))
        checkDebug('Batter current: ' + str(bat_curr_ma))

    try:
        """ Get the lux value from TSL2561 sensor.
        """
        lux = int(tsl.readLux())
        ir = int(tsl.readIR())

    finally:
        checkDebug('Lux: ' + str(lux))
        checkDebug('IR: ' + str(ir))

    if mysqlUpdate == True:
        """ Check config file to see if we are updating the database.
        """
        dbUpdate()
        checkDebug('Database Updated')
    else:
        checkDebug('Database Update Skipped')

    #if dht_temp >= temp_threshold:


    time.sleep(float(interval))


