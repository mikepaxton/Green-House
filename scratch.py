from Adafruit_BME280 import *

sensor = BME280(mode=BME280_OSAMPLE_8)

degrees = sensor.read_temperature()
pascals = sensor.read_pressure()
hectopascals = pascals / 100
humidity = sensor.read_humidity()

def cels_fahr(cels):
    """Function takes in celsius temperature and returns temp in Fahrenheit"""
    temp = cels * 9.0 / 5 + 32
    return temp

temp = cels_fahr(degrees)

print 'Timestamp = {0:0.3f}'.format(sensor.t_fine)
print 'Temp      = {0:0.3f} deg C'.format(temp)
print 'Pressure  = {0:0.2f} hPa'.format(hectopascals)
print 'Humidity  = {0:0.2f} %'.format(humidity)