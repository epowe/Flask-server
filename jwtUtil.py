import time
import jwt

def valid(accessToken):
    try:
        temp = jwt.decode(accessToken, "이에이승팀의샘플비밀키입니다.", algorithms="HS256")
        userIdx = temp["userIdx"]
        exp = temp["exp"]
        if exp < int(time.time()):
            return 401
        else:
            return 200
    except:
        return 401
