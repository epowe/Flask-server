import time
import jwt

def valid(Authorization):
    try:
        type, accessToken = Authorization.split()
        temp = jwt.decode(accessToken, "이에이승팀의샘플비밀키입니다.", algorithms="HS256")
        userIdx = temp["userIdx"]
        exp = temp["exp"]

        if exp < int(time.time()) or type != "Bearer":
            return 401, 0
        else:
            return 200, userIdx
    except:
        return 401, 0
