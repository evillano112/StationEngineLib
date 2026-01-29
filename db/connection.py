import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "radio_user",
    "password": "password",
    "database": "radio_db",
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)
