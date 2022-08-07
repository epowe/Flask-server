# from kospeech.infer_ import pred_sentence
from flask import Flask, request, jsonify
from connections import db_connector
from jwtUtil import valid

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config.from_pyfile('config.py')
db = db_connector()

# 영상 데이터 받아서 사투리 관련 데이터 DB에 저장시키는 API
@app.route('/model/video', methods = ["POST"])
def dialectAnalysis():
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    data = request.get_json()
    title = data["title"]
    question = data["question"]
    videoURL = data["videoURL"]
    print(title)
    print(question)
    print(videoURL)
    return jsonify({"message" : "데이터 저장 완료"}), 200

@app.route('/model/data/score', methods = ["GET"])
def getDataScore():
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
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
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
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
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
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

@app.route('/model/data/list/question', methods = ["GET"])
def getQuestionList():
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")
    try:
        with db.cursor() as cursor:
            query = """
                    select question from video
                    where video_info_id = (select id from VideoInfo where title = '%s' and user_id = %d) 
                        """ % (title, userIdx)
            cursor.execute(query)
            result= cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
    questions = []
    for question in result:
        questions.append(*question)
    json = {
        "questions": questions,
    }
    return jsonify(json), 200

@app.route('/model/data/detail', methods= ["GET"])
def getDataDetail():
    accessToken = request.headers['accessToken']
    status, userIdx = valid(accessToken)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")
    question = request.args.get("question")
    try:
        with db.cursor() as cursor:
            query = """
                    select video.video_url, videoFeedback.dialect_time, videoFeedback.dialect_string, videoFeedback.feedback from Video
                    inner join VideoFeedback on Video.id = VideoFeedback.video_id
                    where video_info_id = (select id from videoInfo where user_id = %d and title = "%s")
                    and video.question = "%s"
                            """ % (userIdx, title, question)
            cursor.execute(query)
            result = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
    videoUrl = ""
    detail = []
    for url, dialectTime, dialectString, feedback in result:
        videoUrl = url
        data = {
            "dialectTime" : str(dialectTime),
            "dialectString" : dialectString,
            "feedback" : feedback
        }
        detail.append(data)

    json = {
        "videoUrl": videoUrl,
        "detail" : detail
    }
    return jsonify(json), 200


if __name__ == "__main__":
    app.run(debug=True)

