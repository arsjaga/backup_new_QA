import pymysql
  
dataBase = pymysql.connect(
  host ="localhost",
  user ="phpmyadmin",
  passwd ="root",
  database = "product_db"
)
 
# preparing a cursor object
cursorObject = dataBase.cursor()
  
# creating table 
studentRecord = """CREATE TABLE STUDENT (
                   S.No INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                   NAME  VARCHAR(20) NOT NULL,
                   BRANCH VARCHAR(50),
                   ROLL INT NOT NULL,
                   SECTION VARCHAR(5),
                   AGE INT
                   )"""
  
# table created
cursorObject.execute(studentRecord) 
  
# disconnecting from server
dataBase.close()