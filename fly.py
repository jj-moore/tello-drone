import sys
import traceback
import tellopy
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import pygame
import pygame.locals
import pygame.key
import threading
import time
import uuid
import av

# custom files
import db_utilities
import joystick_custom
import joystick_predefined

# joystick settings
js_name = None
buttons = None
speed = 100
throttle = 0.0
yaw = 0.0
pitch = 0.0
roll = 0.0

# video settings
new_image = None
current_image = None
run_thread = True

flight_data = None  # log data
drone = None  # Tellopy object
db_row = None  # data to be stored into the database


#  Command line entry point
def main():
    global db_row
    num_args = len(sys.argv)
    db_row = db_utilities.Positional()
    if num_args <= 1:
        print('\n**You must enter at least one command line argument (your name).')
        print('**Optional arguments (in order): group, organization, major')
        print('**Add an "r" as the last argument to resume the previous flight')
        print('**Arguments with spaces must be enclosed in double or single quotes')
        exit(1)
    if num_args > 1:
        db_row.name = sys.argv[1]

    is_resume = False
    if sys.argv[num_args - 1].lower() == 'r':
        is_resume = True
        num_args -= 1

    if num_args > 2:
        db_row.group = sys.argv[2]
    if num_args > 3:
        db_row.org_college = sys.argv[3]
    if num_args > 4:
        db_row.major = sys.argv[4]
    print(db_row)
    initialize(is_resume)


# sets station_id and flight_id, initializes joystick and drone
# starts video thread, starts flight update thread (sets valid to false periodically)
def initialize(is_resume=False):
    db_row.station_id = uuid.uuid3(uuid.NAMESPACE_URL, hex(uuid.getnode()))
    if is_resume:
        row = db_utilities.most_recent_flight_from_station()
        print(f'Continuing flight {row[0]}')
        db_row.flight_id = row[0]
    else:
        print(f'Hello {db_row.name}!')
        db_row.flight_id = uuid.uuid1()

    # initialize_joystick()
    initialize_drone()


# detects joystick and sets buttons
def initialize_joystick():
    global buttons
    global js_name

    pygame.init()
    pygame.joystick.init()
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        if js_name in ('Wireless Controller', 'Sony Computer Entertainment Wireless Controller'):
            buttons = joystick_predefined.JoystickPS4
        elif js_name == 'Sony Interactive Entertainment Wireless Controller':
            buttons = joystick_predefined.JoystickPS4ALT
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controller'):
            buttons = joystick_predefined.JoystickPS3
        elif js_name in 'Logitech Gamepad F310':
            buttons = joystick_predefined.JoystickF310
        elif js_name in ('Xbox One Wired Controller', 'Microsoft X-Box One pad'):
            buttons = joystick_predefined.JoystickXONE
        elif js_name == 'Controller (Xbox One For Windows)':
            buttons = joystick_predefined.JoystickXONE
        elif js_name == 'FrSky Taranis Joystick':
            buttons = joystick_predefined.JoystickTARANIS
        elif js_name is not None:
            buttons = joystick_custom.main(js)
        else:
            print(f'Joystick not recognized. Please try with a different joystick')
            exit(1)
    except pygame.error:
        print(f'Exiting: An error occurred while setting up the joystick. {pygame.get_error()}')
        exit(1)
    print(f'Connected to joystick connected: {js_name}')


# connects to drone, sets log level, adds handlers for event data
def initialize_drone():
    global drone
    drone = tellopy.Tello()
    print(drone.state)
    drone.connect()
    print(f'State: {drone.state}')
    print(f'Wifi: {drone.wifi_strength}')
    drone.subscribe(drone.EVENT_FLIGHT_DATA, flight_data_handler)
    drone.subscribe(drone.EVENT_LOG_DATA, log_data_handler)
    drone.set_loglevel(drone.LOG_WARN)
    if drone.video_enabled:
        threading.Thread(target=video_thread, name='video').start()
    threading.Timer(20.0, db_utilities.update_flight_in_progress, args=[db_row.flight_id])
    run()


# continually listens for joystick events
def run():
    global new_image
    global current_image

    try:
        while True:
            # loop with pygame.event.get() is too much tight w/o some sleep
            time.sleep(0.01)
            for e in pygame.event.get():
                joystick_event_handler(e)
            if current_image is not new_image:
                cv2.imshow('Tello', new_image)
                current_image = new_image
                cv2.waitKey(1)
    except KeyboardInterrupt as e:
        stop()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(e)
        stop()
    stop()


def stop():
    global run_thread
    run_thread = False

    success = input('Was flight successful (y/n)? ')
    print('Updating database ...')
    cv2.destroyAllWindows()
    drone.quit()

    if success.upper() == "N":
        db_utilities.invalidate_flight(db_row.flight_id)
    else:
        db_utilities.validate_flight(db_row.flight_id)

    print(f'Goodbye {db_row.name}')
    exit(0)


def video_thread():
    global new_image
    print('start video_thread()')
    try:
        container = av.open(file=drone.get_video_stream(), mode='r')
        # skip first 300 frames
        frame_skip = 300
        while run_thread:
            for frame in container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                if flight_data:
                    draw_text_on_video(image, 'COSC 480 Drone Competition: ' + str(flight_data), 0)

                new_image = image
                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time)/time_base)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)


def draw_text_on_video(image, text, row):
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


# setting flight data to global handler so it can print later
def flight_data_handler(event, sender, data, **args):
    global flight_data
    flight_data = data


# inserts row if x, y or z changes.
# if flight_data exists, prints it.
def log_data_handler(event, sender, data, **args):
    if db_row is not None:
        cur_x = round(data.mvo.pos_x, 2)
        cur_y = round(data.mvo.pos_y, 2)
        cur_z = round(data.mvo.pos_z, 2)
        #  Only record positional data if different than previous. Cuts down on noise.
        if db_row and (db_row.x != cur_x or db_row.y != cur_y or db_row.z != cur_z):
            db_row.x = cur_x
            db_row.y = cur_y
            db_row.z = cur_z
            db_utilities.insert_record(db_row)
            if flight_data:
                print(f'User: {db_row.name} X: {db_row.x} Y: {db_row.y} Z: {db_row.z} Battery: '
                      f'{flight_data.battery_percentage} Wifi Strength: {flight_data.wifi_strength}')


def joystick_event_handler(e):
    global speed
    global throttle
    global yaw
    global pitch
    global roll
    if e.type == pygame.locals.JOYAXISMOTION:
        # ignore small input values (Deadzone)
        if -buttons.DEADZONE <= e.value <= buttons.DEADZONE:
            e.value = 0.0
        if e.axis == buttons.LEFT_Y:
            throttle = update(throttle, e.value * buttons.LEFT_Y_REVERSE)
            drone.set_throttle(throttle)
        if e.axis == buttons.LEFT_X:
            yaw = update(yaw, e.value * buttons.LEFT_X_REVERSE)
            drone.set_yaw(yaw)
        if e.axis == buttons.RIGHT_Y:
            pitch = update(pitch, e.value * buttons.RIGHT_Y_REVERSE)
            drone.set_pitch(pitch)
        if e.axis == buttons.RIGHT_X:
            roll = update(roll, e.value * buttons.RIGHT_X_REVERSE)
            drone.set_roll(roll)
    elif e.type == pygame.locals.JOYHATMOTION:
        if e.value[0] < 0:
            drone.counter_clockwise(speed)
        if e.value[0] == 0:
            drone.clockwise(0)
        if e.value[0] > 0:
            drone.clockwise(speed)
        if e.value[1] < 0:
            drone.down(speed)
        if e.value[1] == 0:
            drone.up(0)
        if e.value[1] > 0:
            drone.up(speed)

    elif e.type == pygame.locals.JOYBUTTONDOWN:
        if e.button == buttons.LAND:
            drone.land()
        elif e.button == buttons.UP:
            drone.up(speed)
        elif e.button == buttons.DOWN:
            drone.down(speed)
        elif e.button == buttons.ROTATE_RIGHT:
            drone.clockwise(speed)
        elif e.button == buttons.ROTATE_LEFT:
            drone.counter_clockwise(speed)
        elif e.button == buttons.FORWARD:
            drone.forward(speed)
        elif e.button == buttons.BACKWARD:
            drone.backward(speed)
        elif e.button == buttons.RIGHT:
            drone.right(speed)
        elif e.button == buttons.LEFT:
            drone.left(speed)
        elif e.button == buttons.QUIT:
            stop()

    elif e.type == pygame.locals.JOYBUTTONUP:
        if e.button == buttons.TAKEOFF:
            if throttle != 0.0:
                print('###')
                print('### throttle != 0.0 (This may hinder the drone from taking off)')
                print('###')
            drone.takeoff()
        elif e.button == buttons.UP:
            drone.up(0)
        elif e.button == buttons.DOWN:
            drone.down(0)
        elif e.button == buttons.ROTATE_RIGHT:
            drone.clockwise(0)
        elif e.button == buttons.ROTATE_LEFT:
            drone.counter_clockwise(0)
        elif e.button == buttons.FORWARD:
            drone.forward(0)
        elif e.button == buttons.BACKWARD:
            drone.backward(0)
        elif e.button == buttons.RIGHT:
            drone.right(0)
        elif e.button == buttons.LEFT:
            drone.left(0)


def update(old, new, max_delta=0.3):
    if abs(old - new) <= max_delta:
        res = new
    else:
        res = 0.0
    return res


if __name__ == '__main__':
    main()
