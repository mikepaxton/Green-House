import MySQLdb

dbAddress = 'localhost'
dbUser = 'rpi'
dbPassword = '2Fast4uX2'
dbName = 'greenhouse'

con = MySQLdb.connect(host=dbAddress, user=dbUser, passwd=dbPassword, db=dbName)
#c = con.cursor()