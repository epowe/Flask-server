import ssl
import urllib
from config import NAVER_CLOVA_API_KEY_ID, NAVER_CLOVA_API_KEY



def getAiVoice(speaker, text):
    data = "speaker="+ speaker+"&volume=0&speed=0&pitch=0&format=mp3&text=" + text
    url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    context = ssl._create_unverified_context()
    urlRequest = urllib.request.Request(url)
    urlRequest.add_header("X-NCP-APIGW-API-KEY-ID", NAVER_CLOVA_API_KEY_ID)
    urlRequest.add_header("X-NCP-APIGW-API-KEY", NAVER_CLOVA_API_KEY)
    response = urllib.request.urlopen(urlRequest, data=data.encode('utf-8'), context=context)
    resCode = response.getcode()
    if (resCode == 200):
        # print("TTS mp3 저장")
        response_body = response.read()
        return response_body

        # with open('1111.mp3', 'wb') as f:
        #     f.write(response_body)
