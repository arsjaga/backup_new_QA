import pymysql
db = pymysql.connect(host='localhost',user='phpmyadmin',passwd='root')
cursor = db.cursor()
query = ("SHOW DATABASES")
cursor.execute(query)
for r in cursor:
    print (r)



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