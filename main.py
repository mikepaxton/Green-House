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
from TSL2561 import TSL2561
from ConfigParser import SafeConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# TODO: Create a LCD control interface using tkinter or pygame
# TODO: Incorporate Python logging Module into controls
# TODO: Find a logging website other than io.adafruit for greater logging capabilities
# TODO: Work with the TSL2561 light sensor to check for data accuracy
# TODO: Devise a means of checking the battery state before operating the fans
# TODO: Add exhaust_fan_voltage and exhaust_fan_current to mysql database table


# Global stuff
tsl = TSL2561()
config = SafeConfigParser()
config.read('config.cfg')
interval = config.get('defaults', 'interval')  # Get sensor updating interval
debug = config.getboolean('defaults', 'debug')  # debug print to console
ADAFRUIT_IO_KEY = config.get('defaults', 'aio_key')  # Import Adafruit aio Key
aio = Client(ADAFRUIT_IO_KEY)
DHT_TYPE = Adafruit_DHT.DHT22
DHT_PIN = config.get('defaults', 'dht_pin')
mysqlUpdate = config.getboolean('database', 'mysqlUpdate')  # Are we using database?
max_cpu_temp = config.get('defaults', 'max_cpu_temp')
temp_threshold = config.get('fans', 'exhaust_fan_on')
temp_norm = config.get('fans', 'exhaust_fan_off')
circulate_temp = config.get('fans', 'circulate_temp')
message_service = config.getboolean('email', 'send_email')


# Setup and initiate fans on GPIO pins.  Fans should be connected to a relay board.
GPIO.setmode(GPIO.BCM)
exhaust_fan = config.get('fans', int('exhaust_fan_pin'))
GPIO.setup(exhaust_fan, GPIO.OUT)
GPIO.output(exhaust_fan, GPIO.HIGH)
circulate_fan = config.get('fans', int('circulate_fan_pin'))
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
checkDebug('Fan ON Temp: ' + str(temp_threshold))
checkDebug('Fan OFF Temp: ' + str(temp_norm))
checkDebug('Send email messages: ' + str(message_service))


# Main Functions
def dbUpdate():
    """ Open a connection to mysql database using the MySQLdb library.  The database
    can be either local or remote.  If remote you must change both the dbaddress and
    the port number to that of remote. Changed the database connection information
    over to the config file.  Note: dbPort is not implemented in code yet.
    """
    dbAddress = config.get('database', 'dbAddress')
    dbUser = config.get('database', 'dbUser')
    dbPassword = config.get('database', 'dbPassword')
    dbName = config.get('database', 'dbName')
    dbPort = config.get('database', 'dbPort')
    con = MySQLdb.connect(host=dbAddress, Port=dbPort, user=dbUser, passwd=dbPassword,
                          db=dbName)
    c = con.cursor()

    date = datetime.datetime.now()
    c.execute("INSERT INTO sensor_data (date, dht_temp, dht_humidity, cpu_temp, "
              "solar_voltage, solar_current, battery_voltage, battery_current, lux, "
              "ir, exhaust_fan_voltage, exhaust_fan_current) VALUES (%s,%s,%s,%s,%s,%s,"
              "%s,%s,%s,%s,%s,%s)",
              (date, dht_temp, humidity, cpu_temp, sol_volt_v, sol_curr_ma,
               bat_volt_v, bat_curr_ma, lux, ir, exhaust_volt_v, exhaust_curr_ma))

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
    The addresses for the INA219 are: ['0x40', '0x41', '0x44', '0x45']
    """
    for i2caddr in ['0x40']:
        ina = INA219(address=int(i2caddr, 16))
        sol_bus_v = ina.getBusVoltage_V()
        sol_shunt_mv = ina.getShuntVoltage_mV()
        sol_curr_ma = ina.getCurrent_mA()
        sol_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    return sol_volt_v, sol_curr_ma


def getBat():
    """ Gather INA219 sensor readings for Battery"""
    for i2caddr in ['0x41']:
        ina = INA219(address=int(i2caddr, 16))
        bat_bus_v = ina.getBusVoltage_V()
        bat_shunt_mv = ina.getShuntVoltage_mV()
        bat_curr_ma = ina.getCurrent_mA()
        bat_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    return bat_volt_v, bat_curr_ma


def getExhaust():
    """ Gather INA219 sensor readings for the exhaust fan"""
    for i2caddr in ['0x44']:
        ina = INA219(address=int(i2caddr, 16))
        exhaust_bus_v = ina.getBusVoltage_V()
        exhaust_shunt_mv = ina.getShuntVoltage_mV()
        exhaust_curr_ma = ina.getCurrent_mA()
        exhaust_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
    return exhaust_volt_v, exhaust_curr_ma


# Main Loop
try:
    while True:

        # Get CPU temp and send it to aio.  The value is set to two decimal places.
        try:
            getCPUtemp()
            cels = float(getCPUtemp())
            cpu_temp = cels_fahr(cels)
            aio.send('greenhouse-cpu-temp', '{:.2f}'.format(cpu_temp))
        finally:
            checkDebug('CPU Temp: ' + str(cpu_temp))

        # Grab DHT's temp and humidity. Function continues to try getting readings so
        # except passes.  The value is set to two decimal places.
        try:
            dht_temp, humidity = getDHT()
            aio.send('greenhouse-temperature', '{:.2f}'.format(dht_temp))
            aio.send('greenhouse-humidity', '{:.2f}'.format(humidity))
        finally:
            checkDebug('DHT Temp: ' + str(dht_temp))
            checkDebug('DHT Humidity: ' + str(humidity))

        # Get solar panel voltage and current.  The value is set to two decimal places.
        try:
            sol_volt_v, sol_curr_ma = getSolar()
            aio.send('greenhouse-sol-volt', '{:.2f}'.format(sol_volt_v))
            aio.send('greenhouse-sol-current', '{:.2f}'.format(sol_curr_ma))
        finally:
            checkDebug('Solar Panel volts: ' + str(sol_volt_v))
            checkDebug('Solar Panel current: ' + str(sol_curr_ma))

        # Get battery voltage and current.  The value is set to two decimal places.
        try:
            bat_volt_v, bat_curr_ma = getBat()
            aio.send('greenhouse-bat-volt', '{:.2f}'.format(bat_volt_v))
            aio.send('greenhouse-bat-current', '{:.2f}'.format(bat_curr_ma))
        finally:
            checkDebug('Battery volts: ' + str(bat_volt_v))
            checkDebug('Battery current: ' + str(bat_curr_ma))

        # Get exhaust fan voltage and current.  The value is set to two decimal places.
        try:
            exhaust_volt_v, exhaust_curr_ma = getExhaust()
            aio.send('greenhouse-exhaust-volt', '{:.2f}'.format(exhaust_volt_v))
            aio.send('greenhouse-exhaust-current', '{:.2f}'.format(exhaust_curr_ma))
        finally:
            checkDebug('Exhaust Fan volts: ' + str(exhaust_volt_v))
            checkDebug('Exhaust Fan current: ' + str(exhaust_curr_ma))

        # Get the lux value from TSL2561 sensor.
        try:
            lux = int(tsl.readLux())
            ir = int(tsl.readIR())

        finally:
            checkDebug('Lux: ' + str(lux))
            checkDebug('IR: ' + str(ir))

        # Check config file to see if we are updating the database.
        if mysqlUpdate == True:
            dbUpdate()
            checkDebug('Database Updated')
        else:
            checkDebug('Database Update Skipped')

        # Check both temp ranges from config file.  The dht_temp must be equal to or
        # higher than threshold but not lower than the norm for exhaust to run.
        # Must convert both temp ranges to an integer as they are brought from config
        # file as strings.
        if dht_temp >= int(temp_threshold) and dht_temp > int(temp_norm):
            GPIO.output(exhaust_fan, GPIO.LOW)
            checkDebug('Exhaust fans is ON')
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

        # Shutdown the Raspberry Pi if the cpu temp gets to hot.  If message_service is
        # set to True an email message will be sent out so long as there is an Internet
        # connection available. The system will wait for X number of seconds to send
        # the message before shutting down.
        if cpu_temp >= max_cpu_temp:
            if message_service == True:
                message = "The CPU temperature has reached the maximum allowed set in " \
                          " the config file so the system is being shutdown.  This " \
                          "means the fans are no longer working and the plants in the " \
                          "greenhouse are in danger. /n  Please check the system as " \
                          "soon as possible!"
                send_email('Shutdown', message)
                checkDebug('CPU Temp to high, system is shutting down.')
                time.sleep(30)

            GPIO.cleanup()
            os.system('shutdown -h now')
        else:
            continue

        time.sleep(float(interval))

except KeyboardInterrupt:
    GPIO.cleanup()
    checkDebug('Interrupt caught, GPIO.cleanup ran!')
    sys.exit(0)
