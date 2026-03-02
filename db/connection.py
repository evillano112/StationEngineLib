import os
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env file
load_dotenv()

def getConnection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )