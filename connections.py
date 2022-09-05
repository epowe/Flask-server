from config import db
import pymysqlpool
def db_connector():
    pool = pymysqlpool.ConnectionPool(size=5, maxsize=100, pre_create_num=5, name="pool", **db)
    return pool