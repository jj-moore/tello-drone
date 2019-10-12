import sys
import signal
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import pygame
import pygame.locals
import pygame.key
# from subprocess import Popen, PIPE
import threading
import time
import uuid

# custom files
import classes
import db_utilities
import ControllerSetup

js_name = None
buttons = None
drone = None
reset = False
finalize = False
added = True
flight_data = None
prev_flight_data = None
run_recv_thread = True
new_image = None
current_image = None
speed = 100
throttle = 0.0
yaw = 0.0
pitch = 0.0
roll = 0.0

# data to be stored into the database
db_row = None


def main():
    global db_row
    num_args = len(sys.argv)
    db_row = classes.Positional()
    if num_args <= 1:
        print('\n**You must enter at least one command line argument (your name).')
        print('**Optional arguments (in order): group, organization, major')
        print('**Arguments with spaces must be enclosed in double or single quotes')
        exit(1)
    if num_args > 1:
        db_row.name = sys.argv[1]
    if num_args > 2:
        db_row.group = sys.argv[2]
    if num_args > 3:
        db_row.org_college = sys.argv[3]
    if num_args > 4:
        db_row.major = sys.argv[4]
    print(db_row)
    initialize()


def web_start(user):
    global db_row
    db_row = classes.Positional()
    db_row.name = user.name
    db_row.group = user.type
    db_row.org_college = user.organization
    db_row.major = user.major
    initialize()


def web_cancel():
    global db_row
    drone.land()
    db_row = None


def web_stop():
    global db_row
    drone.land()
    statement = db_utilities.flight_success(db_row.flight_id)
    db_utilities.execute_cql(statement)
    db_row = None

    drone.land()
    db_row = None


def initialize():
    print(f'Hello {db_row.name}!')
    db_utilities.connect_to_db()
    db_row.flight_id = uuid.uuid1()
    db_row.station_id = uuid.uuid1()
    pygame.init()
    get_buttons()
    setup_drone()
    run()
    stop()


def get_buttons():
    global buttons
    global reset
    global js_name

    js = None
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        print('Joystick name: ' + js_name)
        if js_name in ('Wireless Controller', 'Sony Computer Entertainment Wireless Controller'):
            buttons = classes.JoystickPS4
        elif js_name == 'Sony Interactive Entertainment Wireless Controller':
            buttons = classes.JoystickPS4ALT
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controller'):
            buttons = classes.JoystickPS3
        elif js_name in 'Logitech Gamepad F310':
            buttons = classes.JoystickF310
        elif js_name in ('Xbox One Wired Controller', 'Microsoft X-Box One pad'):
            buttons = classes.JoystickXONE
        elif js_name == 'Controller (Xbox One For Windows)':
            buttons = classes.JoystickXONE
        elif js_name == 'FrSky Taranis Joystick':
            buttons = classes.JoystickTARANIS
    except pygame.error:
        pass

    if buttons is None and js_name is not None:
        custom_controller = ControllerSetup.main(js)


def setup_drone():
    global drone
    drone = tellopy.Tello()
    drone.connect()
    drone.subscribe(drone.EVENT_FLIGHT_DATA, flight_data_handler)
    drone.subscribe(drone.EVENT_LOG_DATA, log_data_handler)
    threading.Thread(target=recv_thread, args=[drone]).start()


def recv_thread(my_drone):
    global new_image
    global current_image

    try:
        container = av.open(my_drone.get_video_stream())
        while run_recv_thread:
            for frame in container.decode(video=0):
                new_image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                if flight_data:
                    draw_text(new_image, 'TelloPy: ' + str(flight_data), 0)
                if current_image is not new_image:
                    cv2.imshow('Tello', new_image)
                    current_image = new_image
                    cv2.waitKey(1)
    except KeyboardInterrupt:
        stop()
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)


def draw_text(image, text, row):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_size = 24
    font_color = (255, 255, 255)
    bg_color = (0, 0, 0)
    # d = 2
    height, width = image.shape[:2]
    left_mergin = 10
    if row < 0:
        pos = (left_mergin, height + font_size * row + 1)
    else:
        pos = (left_mergin, font_size * (row + 1))
    cv2.putText(image, text, pos, font, font_scale, bg_color, 6)
    cv2.putText(image, text, pos, font, font_scale, font_color, 1)


def update(old, new, max_delta=0.3):
    if abs(old - new) <= max_delta:
        res = new
    else:
        res = 0.0
    return res


def handle_input_event(my_drone, e):
    global speed
    global throttle
    global yaw
    global pitch
    global roll
    global run_recv_thread
    if e.type == pygame.locals.JOYAXISMOTION:
        # ignore small input values (Deadzone)
        if -buttons.DEADZONE <= e.value <= buttons.DEADZONE:
            e.value = 0.0
        if e.axis == buttons.LEFT_Y:
            throttle = update(throttle, e.value * buttons.LEFT_Y_REVERSE)
            my_drone.set_throttle(throttle)
        if e.axis == buttons.LEFT_X:
            yaw = update(yaw, e.value * buttons.LEFT_X_REVERSE)
            my_drone.set_yaw(yaw)

        # ALTERNATIVE RIGHT JOYSTICK
        if e.axis == buttons.RIGHT_Y:
            e.value *= buttons.RIGHT_Y_REVERSE
            if e.value > 0:
                my_drone.forward(speed * abs(e.value))
            elif e.value < 0:
                my_drone.backward(speed * abs(e.value))
        if e.axis == buttons.RIGHT_X:
            e.value *= buttons.RIGHT_X_REVERSE
            if e.value < 0:
                my_drone.left(speed * abs(e.value))
            elif e.value > 0:
                my_drone.right(speed * abs(e.value))

        # ORIGINAL RIGHT JOYSTICK
        # if e.axis == buttons.RIGHT_Y:
        #     pitch = update(pitch, e.value *
        #                    buttons.RIGHT_Y_REVERSE)
        #     drone.set_pitch(pitch)
        # if e.axis == buttons.RIGHT_X:
        #     roll = update(roll, e.value * buttons.RIGHT_X_REVERSE)
        #     drone.set_roll(roll)

    elif e.type == pygame.locals.JOYHATMOTION:
        if e.value[0] < 0:
            my_drone.counter_clockwise(speed)
        if e.value[0] == 0:
            my_drone.clockwise(0)
        if e.value[0] > 0:
            my_drone.clockwise(speed)
        if e.value[1] < 0:
            my_drone.down(speed)
        if e.value[1] == 0:
            my_drone.up(0)
        if e.value[1] > 0:
            my_drone.up(speed)
    elif e.type == pygame.locals.JOYBUTTONDOWN:
        if e.button == buttons.LAND:
            my_drone.land()
        elif e.button == buttons.UP:
            my_drone.up(speed)
        elif e.button == buttons.DOWN:
            my_drone.down(speed)
        elif e.button == buttons.ROTATE_RIGHT:
            my_drone.clockwise(speed)
        elif e.button == buttons.ROTATE_LEFT:
            my_drone.counter_clockwise(speed)
        elif e.button == buttons.FORWARD:
            my_drone.forward(speed)
        elif e.button == buttons.BACKWARD:
            my_drone.backward(speed)
        elif e.button == buttons.RIGHT:
            my_drone.right(speed)
        elif e.button == buttons.LEFT:
            my_drone.left(speed)
        elif e.button == buttons.QUIT:
            my_drone.land()
            run_recv_thread = False
            cv2.destroyAllWindows()
            my_drone.quit()
            exit(1)
    elif e.type == pygame.locals.JOYBUTTONUP:
        if e.button == buttons.TAKEOFF:
            if throttle != 0.0:
                print('###')
                print('### throttle != 0.0 (This may hinder the drone from taking off)')
                print('###')
            my_drone.takeoff()
        elif e.button == buttons.UP:
            my_drone.up(0)
        elif e.button == buttons.DOWN:
            my_drone.down(0)
        elif e.button == buttons.ROTATE_RIGHT:
            my_drone.clockwise(0)
        elif e.button == buttons.ROTATE_LEFT:
            my_drone.counter_clockwise(0)
        elif e.button == buttons.FORWARD:
            my_drone.forward(0)
        elif e.button == buttons.BACKWARD:
            my_drone.backward(0)
        elif e.button == buttons.RIGHT:
            my_drone.right(0)
        elif e.button == buttons.LEFT:
            my_drone.left(0)


def flight_data_handler(event, sender, data, **args):
    print(
        f'Battery %: {data.battery_percentage} Speed: {data.ground_speed} '
        f'Altitude: {data.height} Fly Time: {data.fly_time}')


def log_data_handler(event, sender, data, **args):
    db_row.x = data.mvo.pos_x
    db_row.y = data.mvo.pos_y
    db_row.z = data.mvo.pos_z
    statement = db_utilities.insert_record(db_row)
    db_utilities.execute_cql(statement)


def run():
    global current_image
    global new_image
    global js_name

    try:
        while 1:
            # loop with pygame.event.get() is too much tight w/o some sleep
            time.sleep(0.01)
            for e in pygame.event.get():
                handle_input_event(drone, e)
    except KeyboardInterrupt as e:
        print(e)
        success = input("Was flight successful (y/n)? ")
        if success.upper() == "Y":
            statement = db_utilities.flight_success(db_row.flight_id)
            db_utilities.execute_cql(statement)
        stop()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(e)


def stop():
    global run_recv_thread
    global drone

    run_recv_thread = False
    cv2.destroyAllWindows()
    drone.quit()
    exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop)
    main()
