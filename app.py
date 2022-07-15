from flask import Flask

app = Flask(__name__)

@app.route('/model/dialectAnalysis', methods = ["POST"])
def dialectAnalysis():

    return "json([{},{}])"

@app.route('/model/dialectData', methods = ["GET"])
def new_hello():
    return 'new_hello'