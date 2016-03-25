#!/user/bin/python2
""" This is my Greenhouse Project which takes what I've learned from my SolarPi
Project, the use of solar panels to power a Raspberry Pi system indefinetly.  The
purpose of this project is to control the workings of my greenhouse by
taking various sensor readings then using those readings to control the internal
temperature and humidity of the green house.
The sensors which will be used are the DHT22 for greenhouse temp and humidity. The
INA219 for gathering the voltage and current input of the solar panels and the status
of the batteries along with the current being used by load.
The project will be using a Raspberry Pi for gathering the data and sending it out
using feeds to io.adafruit.com for charting.
Author:  Mike Paxton
Modification date: 03/19/16
"""

import os
import sys
import time
import datetime
import MySQLdb
import smtplib
import Adafruit_DHT
import RPi.GPIO as GPIO
from Adafruit_IO import Client
from Subfact_ina219 import INA219
#from TSL2561 import TSL2561
from ConfigParser import SafeConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ephem
import pytz


# TODO: Find a means of trying to get DHT sensor value repeatedly until captured.
# TODO: Create a LCD control interface using tkinter or pygame
# TODO: Incorporate Python logging Module into controls
# TODO: Find a logging website other than io.adafruit for greater logging capabilities
# TODO: Find a decent light sensor and incorporate it into program
# TODO: Devise a means of checking the battery state before operating the fans
# TODO: Incorporate PowerSwitch Tail to turn a heater on and off
# TODO: Modify fan code so both fans only come on during daylight
# TODO: Create a warning message system for events such as high/low temp, low bat. etc...

# Global config stuff
#tsl = TSL2561()
config = SafeConfigParser()
config.read('config.cfg')
interval = config.getint('defaults', 'interval')  # Get sensor updating interval
debug = config.getboolean('defaults', 'debug')  # debug print to console
ADAFRUIT_IO_KEY = config.get('defaults', 'aio_key')  # Import Adafruit aio Key
aio = Client(ADAFRUIT_IO_KEY)
DHT_TYPE = Adafruit_DHT.DHT22
DHT_PIN = config.getint('defaults', 'dht_pin')
mysqlUpdate = config.getboolean('database', 'mysqlUpdate')  # Are we using database?
max_cpu_temp = config.getint('defaults', 'max_cpu_temp')
exhaustOn = config.getint('environment', 'exhaust_fan_on')
exhaustOff = config.getint('environment', 'exhaust_fan_off')
circulate_temp = config.getint('environment', 'circulate_temp')
message_service = config.getboolean('email', 'send_email')
dayTempHigh = config.getint('environment', 'day_temp_high')
dayTempLow = config.getint('environment', 'day_temp_low')
nightTempHigh = config.getint('environment', 'night_temp_high')
nightTempLow = config.getint('environment', 'night_temp_low')
heaterPin = config.getint('defaults', 'heaterPin')
longitude = config.getfloat('location', 'longitude')
latitude = config.getfloat('location', 'latitude')
altitude = config.getint('location', 'altitude')
tz = config.get('location', 'timezone')

# Setup and initiate fans on GPIO pins.  Fans should be connected to a relay board.
GPIO.setmode(GPIO.BCM)
exhaust_fan = config.getint('environment', 'exhaust_fan_pin')
GPIO.setup(exhaust_fan, GPIO.OUT)
GPIO.output(exhaust_fan, GPIO.HIGH)
circulate_fan = config.getint('environment', 'circulate_fan_pin')
GPIO.setup(circulate_fan, GPIO.OUT)
GPIO.output(circulate_fan, GPIO.HIGH)


def checkDebug(message):
    """ Check for debug status on config file. Function can be called to print debug
    message.  The only parameter is message which you pass a message string.
    """
    if debug == True:
        print(message)


# Debug config file information
checkDebug('Adafruit aio key: ' + str(ADAFRUIT_IO_KEY))
checkDebug('DHT pin used: ' + str(DHT_PIN))
checkDebug('Using Database: ' + str(mysqlUpdate))
checkDebug('Update interval in seconds: ' + str(interval))
checkDebug('Fan ON Temp: ' + str(exhaustOn))
checkDebug('Fan OFF Temp: ' + str(exhaustOff))
checkDebug('Send email messages: ' + str(message_service))
checkDebug('Longitude: ' + str(longitude))
checkDebug('Latitude: ' + str(latitude))
checkDebug('Altitude: ' + str(altitude))
checkDebug('Timezone: ' + str(tz))


# Main Functions
def sunlight():
    """ Using PyEphum to calculate sunrise and sunset
    """
    # Make an observer
    greenhouse = ephem.Observer()

    # PyEphem takes and returns only UTC times.
    greenhouse.date = datetime.datetime.now()
    print ephem.localtime(greenhouse.date)

    greenhouse.lon = str(longitude)
    greenhouse.lat = str(latitude)
    greenhouse.elev = altitude  # Should be in meters

    sunrise = greenhouse.previous_rising(ephem.Sun())
    noon = greenhouse.next_transit(ephem.Sun(), start=sunrise)
    sunset = greenhouse.next_setting(ephem.Sun())
    return sunrise, sunset, noon


def dbUpdate():
    """ Open a connection to mysql database using the MySQLdb library.  The database
    can be either local or remote.  If remote you must change both the dbaddress and
     port number to that of remote. Changed the database connection information
    over to the config file.  Note: dbPort is not implemented in code yet.
    """
    dbAddress = config.get('database', 'dbAddress')
    dbUser = config.get('database', 'dbUser')
    dbPassword = config.get('database', 'dbPassword')
    dbName = config.get('database', 'dbName')
    dbPort = config.getint('database', 'dbPort')
    con = MySQLdb.connect(host=dbAddress, port=dbPort, user=dbUser, passwd=dbPassword,
                          db=dbName)
    c = con.cursor()

    date = datetime.datetime.now()
    c.execute("INSERT INTO sensor_data (date, dht_temp, dht_humidity, cpu_temp, "
              "solar_voltage, solar_current, battery_voltage, battery_current, "
              "load_voltage, load_current) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,"
              "%s)",
              (date, dht_temp, dht_humidity, cpu_temp, sol_volt_v, sol_curr_ma,
               bat_volt_v, bat_curr_ma, load_volt_v, load_curr_ma))

    con.commit()
    con.close()


def send_email(subject, message):
    """ Function to allow sending an email message for various alerts. Two parameters
    need to be passed which are the 'subject' of the message and the 'message' itself.
    The rest of the built-in parameters are defined from the config.cfg file under the
    [email] section and must be set to your needs in order for the function to work
    correctly.
    :param subject:
    :param message:
    """
    email_from = config.get('email', 'email_from')
    email_to = config.get('email', 'email_to')
    email_password = config.get('email', 'email_password')
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject
    body = message
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(config.get('email', 'smtp_server'))
    server.ehlo()
    server.starttls()
    server.login(email_from, email_password)
    text = msg.as_string()
    server.sendmail(email_from, email_to, text)
    server.quit()


def getCPUtemp():
    """Function used to grab RPi CPU Temp and return CPU temperature as a character
    string"""
    res = os.popen('vcgencmd measure_temp').readline()
    return res.replace("temp=", "").replace("'C\n", "")


def cels_fahr(cels):
    """Function takes in celsius temperature and returns temp in Fahrenheit"""
    temp = cels * 9.0 / 5 + 32
    return temp


def getDHT():
    """ Currently only trying to get the DHT sensor value once, if it fails I assign a 0
    value to both the temp and humidity.
    Temp is converted to Fahrenheit.
    """
    dht_humidity, cels = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
    if cels and dht_humidity:
        dht_temp = cels_fahr(cels)
    else:
        checkDebug("*** Unable to get DHT values! ***")
        dht_temp = 0
        dht_humidity = 0
    return dht_temp, dht_humidity


def getLoad():
    """ Gather INA219 sensor readings for Load.
    The addresses for the INA219 are: ['0x40', '0x41', '0x44', '0x45']
    """
    ina = INA219(address=int('0x40', 16))
    load_bus_v = ina.getBusVoltage_V()
    load_shunt_mv = ina.getShuntVoltage_mV()
    load_curr_ma = ina.getCurrent_mA()
    load_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    load_power_mw = ina.getPower_mW()
    return load_volt_v, load_curr_ma


def getSolar():
    """ Gather INA219 sensor readings for Solar Panels.
    The addresses for the INA219 are: ['0x40', '0x41', '0x44', '0x45']
    """
    ina = INA219(address=int('0x44', 16))
    sol_bus_v = ina.getBusVoltage_V()
    sol_shunt_mv = ina.getShuntVoltage_mV()
    sol_curr_ma = ina.getCurrent_mA()
    sol_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    sol_power_mw = ina.getPower_mW()
    return sol_volt_v, sol_curr_ma


def getBat():
    """ Gather INA219 sensor readings for Battery.
    The addresses for the INA219 are: ['0x40', '0x41', '0x44', '0x45']
    """
    ina = INA219(address=int('0x41', 16))
    bat_bus_v = ina.getBusVoltage_V()
    bat_shunt_mv = ina.getShuntVoltage_mV()
    bat_curr_ma = ina.getCurrent_mA()
    bat_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    bat_power_mw = ina.getPower_mW()
    return bat_volt_v, bat_curr_ma

# Main Loop
try:
    while True:

        # Get CPU temp and send it to aio.  The value is set to two decimal places.
        try:
            getCPUtemp()
            cels = float(getCPUtemp())
            cpu_temp = cels_fahr(cels)
            aio.send('greenhouse-cpu-temp', '{:.2f}'.format(cpu_temp))
        except IOError:
            print("Unable to connect to Adafruit.io")
        finally:
            checkDebug('--------------------------')  # Used to separate each interval
            checkDebug('CPU Temp: ' + str(cpu_temp))

        # Shutdown the Raspberry Pi if the cpu temp gets to hot.  If message_service is
        # set to True an email message will be sent out so long as there is an Internet
        # connection available. The system will wait for X number of seconds to send
        # the message before shutting down.
        if cpu_temp >= max_cpu_temp:
            if message_service:
                message = "The CPU temperature of %s has reached the maximum allowed " \
                          "set in the config file, the system is being shutdown.  This " \
                          "means the heating and cooling system is no longer working " \
                          "so the plants in the greenhouse maybe in danger. /n  Please " \
                          "check the system as soon as possible!" % str(cpu_temp)
                send_email('Shutdown', message)
                checkDebug('CPU Temp to high, system is shutting down.')
                time.sleep(15)

            GPIO.cleanup()
            os.system('shutdown -h now')

        # Grab DHT's temp and humidity. Function continues to try getting readings so
        # except passes.  The value is set to two decimal places.  Message Service is
        # then checked.
        try:
            dht_temp, dht_humidity = getDHT()
            if dht_temp != 0:
                aio.send('greenhouse-temperature', '{:.2f}'.format(dht_temp))
                aio.send('greenhouse-humidity', '{:.2f}'.format(dht_humidity))
        except IOError:
            print("Unable to connect to Adafruit.io")
        finally:
            if message_service:
                if dht_temp !=0 and dht_temp <= 40 or dht_temp >= 90:
                    message = "The temperature in the greenhouse is %s.  Please take " \
                              "whatever steps are needed to correct this before the " \
                              "plants are damaged." % str(dht_temp)
                    send_email('Greenhouse temp is to high/low', message)
            if message_service:
                if dht_temp >= 80 and dht_humidity >= 80:
                    message = "The humidity of %s is becoming to high in conjunction " \
                              "with the current temperature of %s. Please take action " \
                              "to  correct this issue." % str(dht_humidity) % str(dht_temp)
                    send_email("High humidity!", message)
            checkDebug('DHT Temp: ' + str(dht_temp))
            checkDebug('DHT Humidity: ' + str(dht_humidity))

        # Get Load voltage and current.  The value is set to two decimal places.
        try:
            load_volt_v, load_curr_ma = getLoad()
            aio.send('greenhouse-load-volt', '{:.2f}'.format(load_volt_v))
            aio.send('greenhouse-load-current', '{:.2f}'.format(load_curr_ma))
        except IOError:
            print("Unable to connect to Adafruit.io")
        finally:
            checkDebug('Load volts: ' + str(load_volt_v))
            checkDebug('Load current: ' + str(load_curr_ma))

        # Get solar panel voltage and current.  The value is set to two decimal places.
        try:
            sol_volt_v, sol_curr_ma = getSolar()
            aio.send('greenhouse-sol-volt', '{:.2f}'.format(sol_volt_v))
            aio.send('greenhouse-sol-current', '{:.2f}'.format(sol_curr_ma))
        except IOError:
            print("Unable to connect to Adafruit.io")
        finally:
            checkDebug('Solar Panel volts: ' + str(sol_volt_v))
            checkDebug('Solar Panel current: ' + str(sol_curr_ma))

        # Get battery voltage and current.  bat_curr_ma is multiplied by -1 to flip
        # the value in order to show the correct current status.  This is done because
        # when the solar panel is charging the battery the value shows as a negative
        # and when not charging shows as a positive.
        # The value is set to two decimal places.
        try:
            bat_volt_v, bat_curr_ma = getBat()
            bat_curr_ma *= -1
            aio.send('greenhouse-bat-volt', '{:.2f}'.format(bat_volt_v))
            aio.send('greenhouse-bat-current', '{:.2f}'.format(bat_curr_ma))
        except IOError:
            print("Unable to connect to Adafruit.io")
        finally:
            checkDebug('Battery volts: ' + str(bat_volt_v))
            checkDebug('Battery current: ' + str(bat_curr_ma))

        # Get the lux value from TSL2561 sensor.
        # try:
        #     lux = int(tsl.readLux())
        #     ir = int(tsl.readIR())
        #
        # finally:
        #     checkDebug('Lux: ' + str(lux))
        #     checkDebug('IR: ' + str(ir))

        # Check config file to see if we are updating the database.
        if mysqlUpdate:
            dbUpdate()
            checkDebug('Database Updated')
        else:
            checkDebug('Database Update Skipped')

        # Check current temp against exhaust fan on and off temp set in config file.
        # The dht_temp must be equal to or higher than exhaustOn but not lower than
        # exhaustOff for fan to run.
        if dht_temp >= exhaustOn and dht_temp > exhaustOff:
            GPIO.output(exhaust_fan, GPIO.LOW)
            checkDebug('Exhaust fan is ON')
        else:
            GPIO.output(exhaust_fan, GPIO.HIGH)
            checkDebug('Exhaust fan is OFF')

        # Check dht_temp against circulate_fan temp and if if need be turn on circulate
        # fan.
        if dht_temp >= circulate_temp:
            GPIO.output(circulate_fan, GPIO.LOW)
            checkDebug('Circulation fan is ON')
        else:
            GPIO.output(circulate_fan, GPIO.HIGH)
            checkDebug('Circulate fan is OFF')
        # Check for sunrise and sunset
        try:
            sunrise, sunset, noon = sunlight()
        finally:
            checkDebug("Sunrise: " + str(sunrise))
            checkDebug("Noon: " + str(noon))
            checkDebug("Sunset: " + str(sunset))

        time.sleep(float(interval))

except KeyboardInterrupt:
    GPIO.cleanup()
    checkDebug('Interrupt caught, GPIO.cleanup ran!')
    sys.exit(0)
