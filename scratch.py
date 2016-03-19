import datetime
from astral import Astral

a = Astral()
a.solar_depression = 'civil'

l = Location(('Lincoln City', 'USA', 44.9722, 124.0111, 'US/Pacific', 0))
l.sun()

city = a[city_name]


print('Information for %s/%s\n' % (city_name, city.region))

sun = city.sun(date=datetime.datetime.now(), local=True)

print('Sunrise: %s' % str(sun['sunrise']))
print('Sunset:  %s' % str(sun['sunset']))