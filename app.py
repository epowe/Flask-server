# from kospeech.infer_ import pred_sentence

from flask import Flask, request
from sqlalchemy import create_engine, text
app = Flask(__name__)
app.config.from_pyfile('config.py')

database = create_engine(app.config['DB_URL'], encoding = 'utf-8')
app.database = database

# 영상 데이터 받아서 사투리 관련 데이터 DB에 저장시키는 API
@app.route('/model/video', methods = ["GET"])
def dialectAnalysis():
    Jwt = request.headers['Jwt']

    print(request.headers['Jwt'])
    return request.get_json()

@app.route('/model/dialectData', methods = ["GET"])
def new_hello():
    return 'new_hello'