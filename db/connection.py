import mysql.connector

def getConnection():
    return mysql.connector.connect(
        host="localhost",
        user="'srv_library_conn'",
        password="xt4l4ct1um",
        database="radio_db"
    )
