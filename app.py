from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, My First Flask!'

@app.route('/hello')
def new_hello():
    return 'new_hello'