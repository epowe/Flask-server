from kospeech.infer_ import pred_sentence

@app.route('/model/dialectAnalysis', methods = ["POST"])
def dialectAnalysis():

    return "json([{},{}])"

@app.route('/model/dialectData', methods = ["GET"])
def new_hello():
    return 'new_hello'
from flask import Flask

s = pred_sentence('a','b','c')
print(s)
# app = Flask(__name__)
#
#
#
# @app.route('/')
# def hello():
#     return 'Hello, My First Flask!'
#
# @app.route('/hello')
# def new_hello():
#     return 'new_hello'
