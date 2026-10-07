import pymysql
  
dataBase = pymysql.connect(
  host ="localhost",
  user ="phpmyadmin",
  passwd ="root",
  database = "product_db"
)
 
# preparing a cursor object
cursorObject = dataBase.cursor()
  
query = "DELETE FROM USB_RELAY WHERE NAME = 'John Doe'"
cursorObject.execute(query)
dataBase.commit()
 
# disconnecting from server
dataBase.close()