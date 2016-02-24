import MySQLdb
import datetime
import time

dht_temp = 100
humidity = 50
cpu_temp = 111
sol_volt_v = 20
sol_curr_ma = 1000
bat_volt_v = 12
bat_curr_ma = 200

while True:
    dbAddress = 'localhost'
    dbUser = 'rpi'
    dbPassword = '2Fast4uX2'
    dbName = 'greenhouse'

    con = MySQLdb.connect(host=dbAddress, user=dbUser, passwd=dbPassword, db=dbName)
    c = con.cursor()

    date = datetime.datetime.now()
    c.execute("INSERT INTO sensor_data (date, dht_temp, dht_humidity, cpu_temp, "
              "solar_voltage, solar_current, battery_voltage, battery_current) VALUES ("
              "%s,%s,%s,%s,%s,%s,%s,%s)", (date, dht_temp, humidity, cpu_temp,
                                           sol_volt_v, sol_curr_ma, bat_volt_v, bat_curr_ma))

    con.commit()

    time.sleep(5)