from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from time import sleep
import tellopy
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


@app.route('/start', methods=['GET', 'POST'])
def test():
    global currentUser
    currentUser = User()
    currentUser.name = request.json.get('name')
    currentUser.type = request.json.get('type')
    currentUser.organization = request.json.get('organization')
    currentUser.major = request.json.get('major')
    fly.web(currentUser)

    # drone = tellopy.Tello()
    # try:
    #     drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
    #     drone.subscribe(drone.EVENT_LOG_DATA, handler)
    #     drone.connect()
    #     drone.wait_for_connection(60.0)
    #     drone.takeoff()
    #     sleep(5)
    #     drone.down(50)
    #     sleep(5)
    #     drone.land()
    #     sleep(5)
    # except Exception as ex:
    #     print(ex)
    # finally:
    #     drone.quit()
    return jsonify(
        message='success'
    )


@app.route('/')
def home():
    return render_template('index.html')
