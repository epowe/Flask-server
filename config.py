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

AWS_ACCESS_KEY_ID=getenv("EPOWE_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=getenv("EPOWE_AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = getenv("AWS_S3_BUCKET_NAME")