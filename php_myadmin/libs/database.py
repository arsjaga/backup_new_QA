from robot.api.deco import keyword
import pymysql
from datetime import datetime


class Database:

    def __init__(self):
        self.host = "localhost"
        self.user = "phpmyadmin"
        self.passwd = "root"
        self.db = None

    @keyword("Connect Database")
    def connect_database(self, database_name):
        try:
            self.db = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=database_name )

        except Exception as e:
            raise Exception(f"Database connection failed: {e}")

    @keyword("Close Database")
    def close_database(self):
        if self.db:
            self.db.close()
            self.db = None
            print("Database connection closed.")

    @keyword("Create Table in Database")
    def create_table_in_database(self):

        if self.db is None:
            raise Exception("Database not connected.")
        cursor = self.db.cursor()

        sql = """CREATE TABLE IF NOT EXISTS USB_RELAY (
                SNo INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                Product_Serial VARCHAR(20) NOT NULL UNIQUE,
                Hardware_Version VARCHAR(50), FTDI_Serial VARCHAR(50),
                Firmware_Version VARCHAR(50), QA_Performed_On DATE,
                QA_Performed_By VARCHAR(50),  QA_Passed VARCHAR(20) );  """

        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    @keyword("Check Table Exists")
    def check_table_exists(self, table_name):

        if self.db is None:
            raise Exception("Database not connected.")

        cursor = self.db.cursor()
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            print(f"Table '{table_name}' exists.")
            return True
        raise Exception(f"Table '{table_name}' does not exist.")

    @keyword("Insert the Values in Table")
    def insert_value_in_table(self, product_serial):

        if self.db is None:
            raise Exception("Database not connected.")

        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM USB_RELAY WHERE Product_Serial=%s", (product_serial,))

        if cursor.fetchone()[0] > 0:
            cursor.close()
            raise Exception(f"Product Serial '{product_serial}' already exists in the Database.")

        cursor.execute("INSERT INTO USB_RELAY (Product_Serial) VALUES (%s)", (product_serial,) )
        self.db.commit()
        cursor.close()


    @keyword("Update Test Data")
    def update_table_value(self, product_serial, column_name, value):

        if self.db is None:
            raise Exception("Database not connected.")

        if column_name == "QA_Performed_On":
            value = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
        cursor = self.db.cursor()
        sql = f"UPDATE USB_RELAY SET {column_name}=%s WHERE Product_Serial=%s"
        cursor.execute(sql, (value, product_serial))

        self.db.commit()
        cursor.close()

    @keyword("Fetch All Records")
    def fetch_all_records(self):

        if self.db is None:
            raise Exception("Database not connected.")

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM USB_RELAY")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    @keyword("Delete Record")
    def delete_record(self, product_serial):

        if self.db is None:
            raise Exception("Database not connected.")

        cursor = self.db.cursor()
        cursor.execute("DELETE FROM USB_RELAY WHERE Product_Serial=%s", (product_serial,))
        self.db.commit()
        cursor.close()



if __name__ == "__main__":

    product = Database()

    product.connect_database("product_db")   # Replace with your database name

    product.create_table_in_database()

    product.check_table_exists("USB_RELAY")

    product.insert_value_in_table()

    product.close_database()