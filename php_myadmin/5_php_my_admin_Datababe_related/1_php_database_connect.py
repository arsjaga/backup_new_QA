import pymysql
db = pymysql.connect(host='localhost',user='phpmyadmin',passwd='root')
cursor = db.cursor()

cursor.execute("CREATE DATABASE product_db")

query = ("SHOW DATABASES")
cursor.execute(query)

for r in cursor:
    print (r)
