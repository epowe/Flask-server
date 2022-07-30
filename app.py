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
        db.close()
    json = {
        "intonation"   : intonation,
        "speechRate"   : speechRate,
        "word"         : word,
        "dialectCount" :dialectCount
    }
    return jsonify(json), 200

@app.route('/model/score/average', methods= ["GET"])
def getDataScoreAverage():
    return ''

@app.route('/model/data/list', methods= ["GET"])
def getDataList():
    return ''

@app.route('/model/data/detail', methods= ["GET"])
def getDataDetail():
    return ''


if __name__ == "__main__":
    app.run(debug=True)

