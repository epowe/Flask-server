from config import db
import pymysql

def db_connector():
    connector = pymysql.connect(**db)
    return connector