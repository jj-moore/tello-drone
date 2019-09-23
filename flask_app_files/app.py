from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from time import sleep
import tellopy
# import PartOne

app = Flask(__name__)
CORS(app)

currentUser = None


class User:
    name = ''
    group = ''
    email = ''
    college = ''
    major = ''


def handler(event, sender, data, **args):
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        print(data)
    if event is drone.EVENT_LOG_DATA:
        print(f'{currentUser.name} {currentUser.group} {currentUser.email} {currentUser.college} {currentUser.major}')
        print(data.mvo)


@app.route('/start', methods=['GET', 'POST'])
def test():
    global currentUser
    # PartOne.main()
    currentUser = User()
    currentUser.name = request.json.get('name')
    currentUser.group = request.json.get('group')
    currentUser.email = request.json.get('email')
    currentUser.college = request.json.get('college')
    currentUser.major = request.json.get('major')

    drone = tellopy.Tello()
    try:
        drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
        drone.subscribe(drone.EVENT_LOG_DATA, handler)
        drone.connect()
        drone.wait_for_connection(60.0)
        drone.takeoff()
        sleep(5)
        drone.down(50)
        sleep(5)
        drone.land()
        sleep(5)
    except Exception as ex:
        print(ex)
    finally:
        drone.quit()
    return jsonify(
        message='success'
    )


@app.route('/')
def home():
    return render_template('index.html')
