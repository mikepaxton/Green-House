    dht_humidity, cels = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
    while cels and dht_humidity == False:
        time.sleep(2)
        dht_humidity, cels = Adafruit_DHT.read(DHT_TYPE, DHT_PIN)
    dht_temp = cels_fahr(cels)
    return dht_temp, dht_humidity