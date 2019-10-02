from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import fly
from user import User

app = Flask(__name__)
CORS(app)
currentUser = None


def handler(event, sender, data, **args):
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        print(f'Battery: {data.battery_percentage}%')
    if event is drone.EVENT_LOG_DATA:
        print(f'X:{data.mvo.pos_x} Y:{data.mvo.pos_y} Z:{data.mvo.pos_z} '
              f'Name: {currentUser.name} Group: {currentUser.group} Email: {currentUser.email} '
              f'College: {currentUser.college} Major: {currentUser.major}')


@app.route('/start', methods=['POST'])
def web_start():
    global currentUser
    currentUser = User()
    currentUser.name = request.json.get('name')
    currentUser.type = request.json.get('type')
    currentUser.organization = request.json.get('organization')
    currentUser.major = request.json.get('major')
    fly.web_start(currentUser)
    return jsonify(
        message='drone started'
    )


@app.route('/finish', methods=['GET'])
def web_stop():
    fly.web_stop()
    return jsonify(
        message='drone stopped'
    )


@app.route('/')
def home():
    return render_template('index.html')
