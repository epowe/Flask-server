from flask import Flask, request, jsonify
from connections import db_connector
from utils.jwtUtil import valid, createToken
from flask_cors import CORS, cross_origin
from extract import feature_extract, replace_str
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME, NAVER_CLOVA_API_KEY, \
    NAVER_CLOVA_API_KEY_ID, ALLOW_ORIGIN
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
CORS(app, resources={r"*": {"origins": ALLOW_ORIGIN}})

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

    speedSum = 0
    wordDict = {}
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
        for i in range(len(words)):
            if not words[i] in wordDict:
                wordDict[words[i]] = wordCount[i]
            else:
                wordDict[words[i]] += wordCount[i]
        # wordList += [(words[i],wordCount[i]) for i in range(len(words))]
        print(detail)
        print(words)
        print(wordCount)
        print(wordDict)
        for i in range(len(detail)):
            detail[i]["dialect_time"] = (datetime.datetime.fromtimestamp(detail[i]["dialect_time"] / 1e3)-datetime.timedelta(hours=9)).strftime("%H:%M:%S.%f")
            detail[i]["dialect_string"] = detail[i]["dialect_string"]

            # 음성 s3 저장
            voiceFilePathInS3 = "voice/" + str(userIdx) + "/" + fileName.replace("%3A", ":")[:-4] + "mp3"
            ttsSound = getAiVoice(speaker, detail[i]["dialect_string"])
            s3_client.put_object(Body=ttsSound, Bucket="epowe-bucket", Key=voiceFilePathInS3)
            detail[i]["voice_url"] = awsBaseUrl + voiceFilePathInS3

        videoAnalysisDatas.append(detail)

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
        # doc = '아부지가 그렇게 갈카주도 와그리 재그람이 없노? 그것도 하나 몬하나?'
        # test = replace_str()
        # print(test.replace_str(detail[0]["dialect_string"]))
    wordList = [(k, v) for k, v in wordDict.items()]
    # wordList.sort(key=lambda x: x[1], reverse=True)
    speedAvg = speedSum/len(question)
    print(wordList)
    print(videoAnalysisDatas)
    try:
        with db.cursor() as cursor:
            query = """
                insert into VideoInfo(user_id, title, speech_rate) values(%d, "%s", %.2f);
                    """ % (userIdx, title, speedAvg)
            cursor.execute(query)
            query = """
                select id from VideoInfo where user_id = %d and title = "%s";
                    """ % (userIdx, title)
            cursor.execute(query)
            videoInfoId = int(cursor.fetchone()[0])
            for i in range(len(wordList)):
                query = """
                    insert into Word(video_info_id, word, count) values(%d, "%s",%d);
                    """ % (videoInfoId, wordList[i][0], wordList[i][1])
                print(query)
                cursor.execute(query)
            for i in range(len(question)):
                query = """
                    insert into Video(video_info_id, question, video_url) values(%d, "%s", "%s");
                        """ % (videoInfoId, question[i], videoURL[i])
                cursor.execute(query)
                query = """
                    select id from Video where video_info_id = %d and question = "%s" and video_url = "%s";
                        """ % (videoInfoId, question[i], videoURL[i])
                cursor.execute(query)
                videoId = int(cursor.fetchone()[0])
                for k in range(len(videoAnalysisDatas[i])):
                    print(videoAnalysisDatas[i][k]["dialect_time"])
                    print(videoAnalysisDatas[i][k]["dialect_string"])
                    query = """
                        insert into VideoFeedback(video_id, dialect_time,dialect_string, voice_url)values(%d, "%s", "%s", "%s");
                            """ % (videoId, videoAnalysisDatas[i][k]["dialect_time"], videoAnalysisDatas[i][k]["dialect_string"], videoAnalysisDatas[i][k]["voice_url"])
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
                select VideoInfo.speech_rate as speechRate, count(*) from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id  
                inner join Video on VideoInfo.id = Video.video_info_id
                inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                where Users.id = %d and VideoInfo.title = '%s'
                group by VideoInfo.speech_rate
                    """ % (userIdx, title)
            cursor.execute(query)
            speechRate, dialectCount = cursor.fetchone()
            query = """
                select Word.word, Word.count from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id
                inner join Word on VideoInfo.id = Word.video_info_id
                where Users.id = %d and VideoInfo.title =  "%s"
                order by count desc limit 1
            """ % (userIdx, title)
            cursor.execute(query)
            word, count = cursor.fetchone()
            db.commit()
    finally:
        cursor.close()
        db.close()
    json = {
        "speechRate"   : speechRate,
        "word"         : word,
        "wordCount" : count,
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
    wordList = []
    try:
        with db.cursor() as cursor:
            getVideoTableQuery = """
                select speech_rate from VideoInfo
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

            getWorListQuery = """
                select Word.word from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id
                inner join Word on VideoInfo.id = Word.video_info_id
                where Users.id = %d
                order by count desc limit 3
            """ % (userIdx)
            cursor.execute(getWorListQuery)
            wordList = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    speechRateArr = []
    for speechRate in result:
        speechRateArr.append(speechRate[0])
    wordArr = []
    for word in wordList:
        wordArr.append(word[0])
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
                    select VideoInfo.title, VideoInfo.speech_rate as speechRate, count(*) from Users
                    inner join VideoInfo on Users.id = VideoInfo.user_id  
                    inner join Video on VideoInfo.id = Video.video_info_id
                    inner join VideoFeedback on Video.id = VideoFeedback.video_id  
                    where Users.id = %d
                    group by VideoInfo.title, VideoInfo.speech_rate
                        """ % (userIdx)
            cursor.execute(query)
            result = cursor.fetchall()
            query = """
                select VideoInfo.title, Word.word, Word.count from Users
                inner join VideoInfo on Users.id = VideoInfo.user_id
                inner join Word on VideoInfo.id = Word.video_info_id
                where Users.id = %d
                order by Word.count          
            """ % (userIdx)
            cursor.execute(query)
            wordResult = cursor.fetchall()
            db.commit()
    finally:
        cursor.close()
        db.close()
    wordDict = {}
    for word in wordResult:
        wordDict[word[0]] = word[1]
    print(wordDict)
    feedbackList = []
    for title, speechRate, dialectCount in result:
        data = {
            "title" : title,
            "speechRate": speechRate,
            "word": wordDict[title],
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
                    select Video.video_url, VideoFeedback.dialect_time, VideoFeedback.dialect_string, VideoFeedback.voice_url from Video
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
    for videoUrl, dialectTime, dialectString, voice_url in result:
        data = {
            "dialectTime" : str(dialectTime),
            "dialectString" : dialectString,
            "voiceUrl" : voice_url
        }
        detail.append(data)
    videoUrl = result[0][0]
    json = {
        "videoUrl": videoUrl,
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

