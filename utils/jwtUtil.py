import time
import jwt
from dotenv import load_dotenv
from os import getenv

load_dotenv()

def valid(Authorization):
    try:
        type, accessToken = Authorization.split()
        temp = jwt.decode(accessToken, getenv("JWT_KEY"), algorithms="HS256")
        userIdx = temp["userIdx"]
        exp = temp["exp"]

        if exp < int(time.time()) or type != "Bearer":
            return 401, 0
        else:
            return 200, int(userIdx)
    except:
        return 401, 0

def createToken(userIdx):
    data = {
        "userIdx": userIdx,
        "exp": int(time.time()) + 3600000
    }
    encoded = jwt.encode(data, getenv("JWT_KEY"), algorithm="HS256")
    return encoded
