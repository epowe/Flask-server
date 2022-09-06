from dotenv import load_dotenv
from os import getenv
load_dotenv()
db = {
    'user' :   getenv("DB_USER"),
    'password' :   getenv("DB_PASSWORD"),
    'host' :   getenv("DB_HOST"),
    'port' :  int(getenv("DB_PORT")),
    'database' :  getenv("DB_NAME"),
    'charset' : 'utf8'
}