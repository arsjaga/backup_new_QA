import pymysql
  
dataBase = pymysql.connect(
  host ="localhost",
  user ="phpmyadmin",
  passwd ="root",
  database = "product_db"
)
 
# preparing a cursor object
cursorObject = dataBase.cursor()
  
query = "UPDATE STUDENT SET AGE = 25 WHERE Name ='Ram'"
cursorObject.execute(query)
dataBase.commit()
 
# disconnecting from server
dataBase.close()