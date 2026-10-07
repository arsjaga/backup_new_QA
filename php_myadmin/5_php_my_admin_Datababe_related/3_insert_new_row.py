import pymysql
  
dataBase = pymysql.connect(
  host ="localhost",
  user ="phpmyadmin",
  passwd ="root",
  database = "product_db"
)
 
# preparing a cursor object
cursorObject = dataBase.cursor()
  
sql = "INSERT INTO STUDENT (Product_Serial, Hardware_Version, FTDI_Serial, Firmware_Version, QA_Performed_On)\
VALUES (%s, %s, %s, %s, %s)"
val = [("Ram", "CSE", "98", "A", "23")]
   
cursorObject.executemany(sql, val)
dataBase.commit()
   
# disconnecting from server
dataBase.close()