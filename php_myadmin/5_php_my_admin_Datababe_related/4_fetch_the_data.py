import pymysql
from tabulate import tabulate

dataBase = pymysql.connect(
    host="localhost",
    user="phpmyadmin",
    passwd="root",
    database="product_db"
)

cursor = dataBase.cursor()

cursor.execute("SELECT * FROM admin")

rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

print(tabulate(rows, headers=columns, tablefmt="grid"))

cursor.close()
dataBase.close()