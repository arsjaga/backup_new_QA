Step 1: Display the Databade in the python 

Code :

    import pymysql
    db = pymysql.connect(host='localhost',user='phpmyadmin',passwd='root')
    cursor = db.cursor()
    query = ("SHOW DATABASES")
    cursor.execute(query)
    for r in cursor:
        print (r)



Issues: to give the permission we want to give the following command.

    sudo mysql
    use mysql;
    CREATE USER 'phpmyadmin'@'localhost' IDENTIFIED BY 'root';
    SET PASSWORD FOR 'phpmyadmin'@'localhost' = PASSWORD('root');
    GRANT ALL PRIVILEGES ON *.* TO 'phpmyadmin'@'localhost' WITH GRANT OPTION;
    FLUSH PRIVILEGES;
    exit


Creating MySQL table using Python

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



Inserting Multiple Rows : 


        import pymysql
        
        dataBase = pymysql.connect(
        host ="localhost",
        user ="user",
        passwd ="password",
        database = "gfg"
        )
        
        # preparing a cursor object
        cursorObject = dataBase.cursor()
        
        sql = "INSERT INTO STUDENT (NAME, BRANCH, ROLL, SECTION, AGE)\
        VALUES (%s, %s, %s, %s, %s)"
        val = [("Nikhil", "CSE", "98", "A", "18"),
            ("Nisha", "CSE", "99", "A", "18"),
            ("Rohan", "MAE", "43", "B", "20"),
            ("Amit", "ECE", "24", "A", "21"),
            ("Anil", "MAE", "45", "B", "20"), 
            ("Megha", "ECE", "55", "A", "22"), 
            ("Sita", "CSE", "95", "A", "19")]
        
        cursorObject.executemany(sql, val)
        dataBase.commit()
        
        # disconnecting from server
        dataBase.close()



Fetch the Data from table: 


        import pymysql
        
        dataBase = pymysql.connect(
        host ="localhost",
        user ="phpmyadmin",
        passwd ="root",
        database = "product_db"
        )
        
        # preparing a cursor object
        cursorObject = dataBase.cursor()
        
        query = "SELECT NAME, ROLL FROM STUDENT"
        cursorObject.execute(query)
        
        myresult = cursorObject.fetchall()
        
        for x in myresult:
            print(x)
        
        # disconnecting from server
        dataBase.close()


Update the Data from table: 


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



Delect the Data from Table:


        import pymysql
        
        dataBase = pymysql.connect(
        host ="localhost",
        user ="phpmyadmin",
        passwd ="root",
        database = "product_db"
        )
        
        # preparing a cursor object
        cursorObject = dataBase.cursor()
        
        query = "DELETE FROM STUDENT WHERE NAME = 'Ram'"
        cursorObject.execute(query)
        dataBase.commit()
        
        # disconnecting from server
        dataBase.close()


