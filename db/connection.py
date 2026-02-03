import mysql.connector

def getConnection():
    return mysql.connector.connect(
        host="localhost",
        user="radio_user",
        password="password",
        database="radio_db"
    )
