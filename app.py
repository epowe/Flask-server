# from kospeech.infer_ import pred_sentence

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from connections import db_connector
import jwt

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = db_connector()
# database = create_engine(app.config['DB_URL'], encoding = 'utf-8')
# app.database = database

json = {
    "userIdx" : 1,
    "userName" : "dongcheon"
}

# 영상 데이터 받아서 사투리 관련 데이터 DB에 저장시키는 API
@app.route('/model/video', methods = ["POST"])
def dialectAnalysis():
    Jwt = request.headers['Jwt']

    title = request.get_data().title
    question = request.get_data().question
    videoURL = request.get_data().videoURL


    print(title)
    print(question)
    print(videoURL)
    print(request.headers['Jwt'])
    return request.get_json()

@app.route('/model/data/score', methods = ["GET"])
def getDataScore():
    userToken = request.headers['userToken']
    data = jwt.decode(userToken, "asdlfjasdfasd", algorithms= "HS256")
    userIdx = data["userIdx"]
    title = request.args.get("title")
    try:
        with db.cursor() as cursor:
            query = """
                select videoInfo.intonation as intonation, videoInfo.speech_rate as speechRate, videoInfo.word as word, count(*) from users
                inner join VideoInfo on users.id = VideoInfo.user_id  
                inner join Video on VideoInfo.id = Video.video_info_id
                inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                where users.id = %d and videoInfo.title = '%s'
                group by videoInfo.intonation, videoInfo.speech_rate, videoInfo.word
                    """ % (userIdx, title)
            cursor.execute(query)
            intonation, speechRate, word, dialectCount = cursor.fetchone()
            db.commit()
    finally:
        cursor.close()
    json = {
        "intonation"   : intonation,
        "speechRate"   : speechRate,
        "word"         : word,
        "dialectCount" : dialectCount
    }
    return jsonify(json), 200

@app.route('/model/score/average', methods= ["GET"])
def getDataScoreAverage():
    userToken = request.headers['userToken']
    data = jwt.decode(userToken, "asdlfjasdfasd", algorithms="HS256")
    userIdx = data["userIdx"]
    try:
        with db.cursor() as cursor:
            getVideoTableQuery = """
                select speech_rate, intonation, word from videoInfo
                where user_Id = %s
                    """
            getDialectCountQuery = """
                select count(VideoFeedback.id)from users
                inner join VideoInfo on users.id = VideoInfo.user_id  
                inner join Video on VideoInfo.id = Video.video_info_id
                inner join VideoFeedback on Video.id = VideoFeedback.video_id
                where user_Id = %d
            """ % (userIdx)
            cursor.execute(getVideoTableQuery, (userIdx, ))
            result = cursor.fetchall()
            cursor.execute(getDialectCountQuery)
            dialectCount = cursor.fetchone()[0]
            db.commit()
    finally:
        cursor.close()
    speechRateArr = []
    intonationArr = []
    wordArr = []
    for speechRate, intonation, word in result:
        speechRateArr.append(speechRate)
        intonationArr.append(intonation)
        wordArr.append(word)
    videoCount = len(result)
    speechRateAvg = sum(speechRateArr)/videoCount
    intonationAvg = sum(intonationArr)/videoCount
    dialectCountAvg = dialectCount/videoCount
    json = {
        "speechRateAvg" : speechRateAvg,
        "intonationAvg" : intonationAvg,
        "dialectCountAvg" : dialectCountAvg,
        "wordArr" : wordArr
    }
    return jsonify(json), 200

@app.route('/model/data/list', methods= ["GET"])
def getDataList():
    userToken = request.headers['userToken']
    data = jwt.decode(userToken, "asdlfjasdfasd", algorithms="HS256")
    userIdx = data["userIdx"]
    try:
        with db.cursor() as cursor:
            query = """
                    select videoinfo.title, videoInfo.intonation as intonation, videoInfo.speech_rate as speechRate, videoInfo.word as word, count(*) from users
                    inner join VideoInfo on users.id = VideoInfo.user_id  
                    inner join Video on VideoInfo.id = Video.video_info_id
                    inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                    where users.id = %d
                    group by videoinfo.title, videoInfo.intonation, videoInfo.speech_rate, videoInfo.word
                        """ % (userIdx)
            cursor.execute(query)
            result = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
    feedbackList = []
    for title, intonation, speechRate, word, dialectCount in result:
        data = {
            "title" : title,
            "intonation": intonation,
            "speechRate": speechRate,
            "word": word,
            "dialectCount": dialectCount
        }
        feedbackList.append(data)
    json = {
        "feedbackList" : feedbackList
    }
    return jsonify(json), 200


@app.route('/model/data/detail', methods= ["GET"])
def getDataDetail():
    return ''


if __name__ == "__main__":
    app.run(debug=True)

