from flask import Flask, request, jsonify
from connections import db_connector
from utils.jwtUtil import valid, createToken
from flask_cors import CORS, cross_origin
from extract import feature_extract
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME, NAVER_CLOVA_API_KEY, NAVER_CLOVA_API_KEY_ID
from utils.ttsUtil import *
import pydub
import boto3
import datetime
import os
import shutil

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config.from_pyfile('config.py')
dbConnectionPool = db_connector()
CORS(app, resources={r"*": {"origins": "*"}})

s3_client = boto3.client(service_name="s3",
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

@app.route('/model/video', methods = ["POST"])
@cross_origin()
def dialectAnalysis():


    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    data = request.get_json()
    title = data["title"]
    question = data["question"]
    videoURL = [URL.replace("%3A", ":") for URL in data["videoURL"]]
    speaker = data["speaker"]

    voiceURLArr = []

    speedSum = 0
    wordList = []
    videoAnalysisDatas = []

    for URL in videoURL:
        fileName = URL.split("/")[-1].replace("%3A", ":")
        awsBaseUrl = "/".join(URL.split("/")[:3]) + "/"
        filePath = "kospeech/data/video/" + fileName

        originalSoundPath = filePath[:-4]+"mp3"
        s3_client.download_file(AWS_S3_BUCKET_NAME, "upload/"+fileName, filePath)

        # ai 모델 영상 분석
        extractor = feature_extract()
        extractor.audio(filePath)
        analysisData = extractor.extract(create_path=fileName[:-4]+"csv")

        # 음성 파일 mp3 변환
        sound = pydub.AudioSegment.from_wav(filePath[:-4]+"wav")
        sound.export(originalSoundPath, format="mp3")

        #분석 데이터 처리
        speedSum += analysisData["speed"]
        detail = analysisData["detail"]
        words = analysisData["words"]
        wordCount = analysisData["words_count"]
        wordList += [(words[i],wordCount[i]) for i in range(len(words))]

        for i in range(len(detail)):
            detail[i]["dialect_time"] = (datetime.datetime.fromtimestamp(detail[i]["dialect_time"] / 1e3)-datetime.timedelta(hours=9)).strftime("%H:%M:%S.%f")
            detail[i]["dialect_string"] = detail[i]["dialect_string"]

        videoAnalysisDatas.append(detail)

        # 음성 s3 저장
        originalVoiceFilePathInS3 = "voice/original/" + fileName.replace("%3A", ":")[:-4] + "mp3"
        ttsVoiceFilePathInS3 = "voice/tts/" + fileName.replace("%3A", ":")[:-4] + "mp3"
        voiceURLArr.append([awsBaseUrl + originalVoiceFilePathInS3, awsBaseUrl + ttsVoiceFilePathInS3])

        ttsSound = getAiVoice(speaker, detail[0]["dialect_string"])
        s3_client.upload_file(originalSoundPath, "epowe-bucket", originalVoiceFilePathInS3)
        s3_client.put_object(Body=ttsSound, Bucket="epowe-bucket", Key=ttsVoiceFilePathInS3)

        # 만든 파일 삭제
        if os.path.isfile(filePath):
            os.remove(filePath)
        if os.path.isfile(filePath[:-3] + "av"):
            os.remove(filePath[:-3] + "av")
        if os.path.isfile(originalSoundPath):
            os.remove(originalSoundPath)
        if os.path.isdir(filePath[:-5]):
            shutil.rmtree(filePath[:-5], ignore_errors=True)
        if os.path.isfile(fileName[:-4]+"csv"):
            os.remove(fileName[:-4]+"csv")

    wordList.sort(key=lambda x: x[1], reverse=True)
    speedAvg = speedSum/len(question)

    try:
        with db.cursor() as cursor:
            query = """
                insert into VideoInfo(user_id, title, speech_rate, word) values(%d, "%s", %.2f, "%s");
                    """ % (userIdx, title, speedAvg, wordList[0][0])
            cursor.execute(query)
            query = """
                select id from VideoInfo where user_id = %d and title = "%s";
                    """ % (userIdx, title)
            cursor.execute(query)
            videoInfoId = int(cursor.fetchone()[0])
            for i in range(len(question)):
                query = """
                    insert into Video(video_info_id, question, video_url, original_voice_url, ai_voice_url) values(%d, "%s", "%s", "%s", "%s");
                        """ % (videoInfoId, question[i], videoURL[i], voiceURLArr[i][0], voiceURLArr[i][1])
                cursor.execute(query)
                query = """
                    select id from Video where video_info_id = %d and question = "%s" and video_url = "%s";
                        """ % (videoInfoId, question[i], videoURL[i])
                cursor.execute(query)
                videoId = int(cursor.fetchone()[0])
                for feedback in videoAnalysisDatas[i]:
                    query = """
                        insert into VideoFeedback(video_id, dialect_time,dialect_string,feedback)values(%d, "%s", "%s", "%s");
                            """ % (videoId, feedback["dialect_time"], feedback["dialect_string"], "test")
                    cursor.execute(query)
            db.commit()
    finally:
        cursor.close()
        db.close()
    return jsonify({"message" : "데이터 저장 완료"}), 200

@app.route('/model/data/score', methods = ["GET"])
@cross_origin()
def getDataScore():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")

    try:
        with db.cursor() as cursor:
            query = """
                select VideoInfo.speech_rate as speechRate, VideoInfo.word as word, count(*) from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id  
                inner join Video on VideoInfo.id = Video.video_info_id
                inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                where Users.id = %d and VideoInfo.title = '%s'
                group by VideoInfo.speech_rate, VideoInfo.word
                    """ % (userIdx, title)
            cursor.execute(query)
            speechRate, word, dialectCount = cursor.fetchone()
            db.commit()
    finally:
        cursor.close()
        db.close()
    json = {
        "speechRate"   : speechRate,
        "word"         : word,
        "dialectCount" : dialectCount
    }
    return jsonify(json), 200

@app.route('/model/score/average', methods= ["GET"])
@cross_origin()
def getDataScoreAverage():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    try:
        with db.cursor() as cursor:
            getVideoTableQuery = """
                select speech_rate, word from VideoInfo
                where user_Id = %s
                    """
            getDialectCountQuery = """
                select count(VideoFeedback.id)from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id  
                inner join Video on VideoInfo.id = Video.video_info_id
                inner join VideoFeedback on Video.id = VideoFeedback.video_id
                where user_id = %d
            """ % (userIdx)
            cursor.execute(getVideoTableQuery, (userIdx, ))
            result = cursor.fetchall()
            cursor.execute(getDialectCountQuery)
            dialectCount = cursor.fetchone()[0]
            db.commit()
    finally:
        cursor.close()
        db.close()
    speechRateArr = []
    wordArr = []
    for speechRate, word in result:
        speechRateArr.append(speechRate)
        wordArr.append(word)
    videoCount = len(result)
    speechRateAvg = sum(speechRateArr)/videoCount
    dialectCountAvg = dialectCount/videoCount
    json = {
        "speechRateAvg" : speechRateAvg,
        "dialectCountAvg" : dialectCountAvg,
        "wordArr" : wordArr
    }
    return jsonify(json), 200

@app.route('/model/data/list', methods= ["GET"])
@cross_origin()
def getDataList():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    try:
        with db.cursor() as cursor:
            query = """
                    select VideoInfo.title, VideoInfo.speech_rate as speechRate, VideoInfo.word as word, count(*) from Users
                    inner join VideoInfo on Users.id = VideoInfo.user_id  
                    inner join Video on VideoInfo.id = Video.video_info_id
                    inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                    where Users.id = %d
                    group by VideoInfo.title, VideoInfo.speech_rate, VideoInfo.word
                        """ % (userIdx)
            cursor.execute(query)
            result = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    feedbackList = []
    for title, speechRate, word, dialectCount in result:
        data = {
            "title" : title,
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
@cross_origin()
def getQuestionList():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")
    try:
        with db.cursor() as cursor:
            query = """
                    select question from Video
                    where video_info_id = (select id from VideoInfo where title = '%s' and user_id = %d) 
                        """ % (title, userIdx)
            cursor.execute(query)
            result= cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    questions = []
    for question in result:
        questions.append(*question)
    json = {
        "questions": questions,
    }
    return jsonify(json), 200

@app.route('/model/data/detail', methods= ["GET"])
@cross_origin()
def getDataDetail():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")
    question = request.args.get("question")
    try:
        with db.cursor() as cursor:
            query = """
                    select Video.video_url,Video.original_voice_url, Video.ai_voice_url, VideoFeedback.dialect_time, VideoFeedback.dialect_string, VideoFeedback.feedback from Video
                    inner join VideoFeedback on Video.id = VideoFeedback.video_id
                    where video_info_id = (select id from VideoInfo where user_id = %d and title = "%s")
                    and Video.question = "%s"
                            """ % (userIdx, title, question)
            cursor.execute(query)
            result = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    detail = []
    for videoUrl, originalVoiceUrl, aiVoiceUrl, dialectTime, dialectString, feedback in result:

        data = {
            "dialectTime" : str(dialectTime),
            "dialectString" : dialectString,
            "feedback" : feedback
        }
        detail.append(data)

    videoUrl = result[0][0]
    originalVoiceUrl = result[0][1]
    aiVoiceUrl = result[0][2]

    json = {
        "videoUrl": videoUrl,
        "originalVoiceUrl" : originalVoiceUrl,
        "aiVoiceUrl" : aiVoiceUrl,
        "detail" : detail
    }
    return jsonify(json), 200

@app.route('/model/check/title', methods = ['GET'])
@cross_origin()
def getCheckTitle():
    db = dbConnectionPool.get_connection()
    Authorization = request.headers['Authorization']
    status, userIdx = valid(Authorization)
    if status == 401:
        return jsonify({"message": "유효하지 않은 토큰입니다."}), 401
    title = request.args.get("title")

    try:
        with db.cursor() as cursor:
            query = """
                    select * from VideoInfo
                    where user_id = %d and title = "%s"
                """ % (userIdx, title)
            cursor.execute(query)
            result = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    if result:
        return jsonify({"message" : "중복되는 제목입니다."}), 400
    else:
        return jsonify({"message" : "사용 가능한 제목입니다."}), 200

@app.route('/model/test/token', methods = ['GET'])
def getTestToken():
    userIdx = int(request.args.get("userIdx"))
    json = {
        "token": createToken(userIdx= userIdx)
    }
    return jsonify(json), 200

if __name__ == "__main__":
    app.run(debug=True)

