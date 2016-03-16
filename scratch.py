from Subfact_ina219 import INA219
import time


def getLoad():
    """ Gather INA219 sensor readings for Solar Panels.
    The addresses for the INA219 are: ['0x40', '0x41', '0x44', '0x45']
    """
    for i2caddr in ['0x40']:
        ina = INA219(address=int(i2caddr, 16))
        load_bus_v = ina.getBusVoltage_V()
        load_shunt_mv = ina.getShuntVoltage_mV()
        load_curr_ma = ina.getCurrent_mA()
        load_volt_v = (ina.getBusVoltage_V() + ina.getShuntVoltage_mV() / 1000)
        load_power_mw = ina.getPower_mW()
        print('Load bus: ' + str(load_bus_v))
        print('Load Shunt: ' + str(load_shunt_mv))
        print('Load Volt: ' + str(load_volt_v))
        print('Load Current: ' + str(load_curr_ma))
        print('Load Power (mW): ' + str(load_power_mw))
        print('-----------------------')
    return load_volt_v, load_curr_ma

while True:
    getLoad()

    time.sleep(5)