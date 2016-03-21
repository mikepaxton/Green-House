--------------------------
CPU Temp: 100.22
DHT Temp: 68.3600013733
DHT Humidity: 72.3000030518
Traceback (most recent call last):
  File "/home/pi/Projects/Greenhouse/main.py", line 249, in <module>
    dht_temp, dht_humidity = getDHT()
  File "/home/pi/Projects/Greenhouse/main.py", line 169, in getDHT
    dht_temp = cels_fahr(cels)
  File "/home/pi/Projects/Greenhouse/main.py", line 153, in cels_fahr
    temp = cels * 9.0 / 5 + 32
TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'