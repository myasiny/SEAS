import sqlite3
from flaskext.mysql import MySQL
from passlib.apps import custom_app_context as pwd_context


class SqlLiteDB:
    def __init__(self, dbName):
        if ".db" not in dbName:
            self.db = sqlite3.connect(dbName+".db")
        else:
            self.db = sqlite3.connect(dbName)
        self.cursor = self.db.cursor()

    def createTable(self, tableName, **columnNames):
        columns = ""
        for i in columnNames:
            columns += "%s %s, " %(i, columnNames[i])
        columns = columns[0:len(columns)-2]
        tableName = tableName.replace(" ", "_")
        command = "create table if not exists %s (%s)" %(tableName, columns)
        self.cursor.execute(command)
        self.__commit()

    def deleteTable(self, tableName):
        command = "Drop table if exists %s" %(tableName)
        self.cursor.execute(command)

    def execute(self, command, *values):
        rtn = self.cursor.execute(command, values).fetchall()
        self.__commit()
        return rtn

    def __commit(self):
        self.db.commit()


class MySQLdb:
    def __init__(self, dbName, app, user="admin", password="1234"):
        mysql = MySQL()
        app.config['MYSQL_DATABASE_USER'] = "admin"
        app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
        app.config['MYSQL_DATABASE_DB'] = dbName
        app.config['MYSQL_DATABASE_HOST'] = 'localhost'
        app.config['MYSQL_DATABASE_PORT'] = 8000
        self.name = dbName

        mysql.init_app(app)

        self.db = mysql.connect()
        self.cursor = self.db.cursor()

        self.execute("CREATE TABLE IF NOT EXISTS Organizations "
                   "( "
                   "Name CHAR(40) NOT NULL, "
                   "ID INT NOT NULL AUTO_INCREMENT, "
                   "PRIMARY KEY (ID),"
                   "UNIQUE (Name) )")

        self.execute("CREATE TABLE IF NOT EXISTS Roles "
                        "( "
                        "Name CHAR(40) NOT NULL, "
                        "ID INT NOT NULL AUTO_INCREMENT, "
                        "PRIMARY KEY (ID),"
                        "UNIQUE (Name) "
                        ")")
        try:
            for i in ["admin", "student", "lecturer"]:
                self.execute("INSERT INTO Roles ( Name ) values ('%s')" %i)
        except:
            pass


    def execute(self, command):
        # print command
        self.cursor.execute(command)

        rtn = self.cursor.fetchone()
        self.__commit()
        return rtn

    def __commit(self):
        self.db.commit()


class Password:
    def hashPassword(self, password):
        self.password_hash = pwd_context.encrypt(password)
        return self.password_hash
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)
    def verify_password_hash(self, password, hashed_password):
        return pwd_context.verify(password, hashed_password)

if __name__ == "__main__":
    a = Password("12345")
    a.hashPassword()
    print a.verify_password("1234")