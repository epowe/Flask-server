from config import db
import pymysqlpool
def db_connector():
    pool = pymysqlpool.ConnectionPool(size=20, maxsize=100, pre_create_num=10, name="pool", **db)
    return pool