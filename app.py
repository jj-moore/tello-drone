from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import fly
from classes import WebUser

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def web_start():
    current_user = WebUser()
    current_user.name = request.json.get('name')
    current_user.type = request.json.get('type')
    current_user.organization = request.json.get('organization')
    current_user.major = request.json.get('major')
    fly.web_start(current_user)
    return jsonify(
        message='drone started'
    )


@app.route('/finish', methods=['GET'])
def web_stop():
    fly.web_stop()
    return jsonify(
        message='drone stopped'
    )
