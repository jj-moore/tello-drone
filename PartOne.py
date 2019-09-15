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
from subprocess import Popen, PIPE
import threading
import time

js_name = None
buttons = None
drone = None
reset = False
finalize = False
added = True
prev_flight_data = None
run_recv_thread = True
new_image = None
flight_data = None
current_image = None
speed = 100
throttle = 0.0
yaw = 0.0
pitch = 0.0
roll = 0.0


class JoystickPS3:
    # d-pad
    UP = 4  # UP
    DOWN = 6  # DOWN
    ROTATE_LEFT = 7  # LEFT
    ROTATE_RIGHT = 5  # RIGHT

    # bumper triggers
    TAKEOFF = 11  # R1
    LAND = 10  # L1
    # UNUSED = 9 #R2
    # UNUSED = 8 #L2

    # buttons
    FORWARD = 12  # TRIANGLE
    BACKWARD = 14  # CROSS
    LEFT = 15  # SQUARE
    RIGHT = 13  # CIRCLE

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.01


class JoystickPS4:
    # d-pad
    UP = -1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -1  # LEFT
    ROTATE_RIGHT = -1  # RIGHT

    # bumper triggers
    TAKEOFF = 5  # R1
    LAND = 4  # L1
    # UNUSED = 7 #R2
    # UNUSED = 6 #L2

    # buttons
    FORWARD = 3  # TRIANGLE
    BACKWARD = 1  # CROSS
    LEFT = 0  # SQUARE
    RIGHT = 2  # CIRCLE

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.08


class JoystickPS4ALT:
    # d-pad
    UP = -1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -1  # LEFT
    ROTATE_RIGHT = -1  # RIGHT

    # bumper triggers
    TAKEOFF = 5  # R1
    LAND = 4  # L1
    # UNUSED = 7 #R2
    # UNUSED = 6 #L2

    # buttons
    FORWARD = 3  # TRIANGLE
    BACKWARD = 1  # CROSS
    LEFT = 0  # SQUARE
    RIGHT = 2  # CIRCLE

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 3
    RIGHT_Y = 4
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.08


class JoystickF310:
    # d-pad
    UP = -1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -1  # LEFT
    ROTATE_RIGHT = -1  # RIGHT

    # bumper triggers
    TAKEOFF = 5  # R1
    LAND = 4  # L1
    # UNUSED = 7 #R2
    # UNUSED = 6 #L2

    # buttons
    FORWARD = 3  # Y
    BACKWARD = 0  # B
    LEFT = 2  # X
    RIGHT = 1  # A

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 3
    RIGHT_Y = 4
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.08


class JoystickXONE:
    # d-pad
    UP = 0  # UP
    DOWN = 1  # DOWN
    ROTATE_LEFT = 2  # LEFT
    ROTATE_RIGHT = 3  # RIGHT

    # bumper triggers
    TAKEOFF = 9  # RB
    LAND = 8  # LB
    # UNUSED = 7 #RT
    # UNUSED = 6 #LT

    # buttons
    FORWARD = 14  # Y
    BACKWARD = 11  # A
    LEFT = 13  # X
    RIGHT = 12  # B

    # axis
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.09


class JoystickTARANIS:
    # d-pad
    UP = -1  # UP
    DOWN = -1  # DOWN
    ROTATE_LEFT = -1  # LEFT
    ROTATE_RIGHT = -1  # RIGHT

    # bumper triggers
    TAKEOFF = 12  # left switch
    LAND = 12  # left switch
    # UNUSED = 7 #RT
    # UNUSED = 6 #LT

    # buttons
    FORWARD = -1
    BACKWARD = -1
    LEFT = -1
    RIGHT = -1

    # axis
    LEFT_X = 3
    LEFT_Y = 0
    RIGHT_X = 1
    RIGHT_Y = 2
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = 1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = 1.0
    DEADZONE = 0.01


class CustomController:
    TAKEOFF = None
    LAND = None
    UP = None
    DOWN = None
    ROTATE_RIGHT = None
    ROTATE_LEFT = None
    FORWARD = None
    BACKWARD = None
    RIGHT = None
    LEFT = None
    DEADZONE = 0.1
    LEFT_X = None
    LEFT_Y = None
    RIGHT_X = None
    RIGHT_Y = None
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = 1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = 1.0


    def __init__(self, control_set):
        number_of_controls = len(control_set)
        self.TAKEOFF = control_set[0]
        self.LAND = control_set[1]

        if number_of_controls > 2:
            self.UP = control_set[2]
        if number_of_controls > 3:
            self.DOWN = control_set[3]
        if number_of_controls > 4:
            self.ROTATE_RIGHT = control_set[4]
        if number_of_controls > 5:
            self.ROTATE_LEFT = control_set[5]
        if number_of_controls > 6:
            self.FORWARD = control_set[6]
        if number_of_controls > 7:
            self.BACKWARD = control_set[7]
        if number_of_controls > 8:
            self.RIGHT = control_set[8]
        if number_of_controls > 9:
            self.LEFT = control_set[9]


def main():
    pygame.init()
    get_buttons()
    setup_drone()
    run()
    stop()


def get_buttons():
    global buttons
    global reset
    global js_name

    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        js_name = js.get_name()
        print('Joystick name: ' + js_name)
        if js_name in ('wireless Controller', 'Sony Computer Entertainment Wireless Controller'):
            buttons = JoystickPS4
        elif js_name == 'Sony Interactive Entertainment Wireless Controller':
            buttons = JoystickPS4ALT
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controller'):
            buttons = JoystickPS3
        elif js_name in ('Logitech Gamepad F310'):
            buttons = JoystickF310
        elif js_name == 'Xbox One Wired Controller':
            buttons = JoystickXONE
        elif js_name == 'Controller (Xbox One For Windows)':
            buttons = JoystickXONE
        elif js_name == 'FrSky Taranis Joystick':
            buttons = JoystickTARANIS
    except pygame.error:
        pass


    if buttons is None and js_name is not None:
        print('No supported controller found, initializing custom controller.')
        while True:
            new_controller(js)
            if not reset:
                break
            reset = False


def new_controller(js):
    global buttons
    global added

    print('This is a set up for your controller. If at anytime you want to restart, simply press the Takeoff button. '
          'After setting a Takeoff and Land button, press the Land button to finalize the selected buttons.')
    control_set = []
    print('Select Takeoff button.')
    control_set.append(get_input())

    controls = ['Land', 'Up', 'Down', 'Rotate right', 'Rotate left', 'Forward', 'Backward', 'Right', 'Left']

    for action in controls:
        while True:
            added = True
            add_control(action, control_set)
            if added:
                break
        if reset:
            control_set.clear()
            return
        if finalize:
            break

    buttons = CustomController(control_set)
    set_deadzone()

#wrong number of joysticks
    number_of_joystick = js.get_numaxes()
    print(number_of_joystick)
    if number_of_joystick is 1:
        setup_one_joystick()
    elif number_of_joystick >=2:
        setup_two_joystick()



def add_control(action, control_set):
    global reset
    global finalize
    global added

    print('Select ' + action + ' button.')
    control = get_input()
    if control == control_set[0]:
        reset = True
    if len(control_set) > 1:
        if control == control_set[1]:
            finalize = True

    if not finalize and not reset:
        for items in control_set:
            if control == items:
                print('Repeated button value, try again')
                added = False

    control_set.append(control)
    return True


def get_input():
    pygame.event.clear()
    pygame.event.wait()
    while True:
        for e in pygame.event.get():
           # if abs(e.value) > .1:
          #      print(e.axis)
            if e.type == pygame.locals.JOYBUTTONDOWN:
                return e.button


def setup_one_joystick():
    print('Push joystick up')
    left_y_list = get_axis()
    buttons.LEFT_Y = left_y_list[0]
    if left_y_list[1] < 0:
        buttons.LEFT_Y_REVERSE = -1

    print('Push joystick to the right')
    left_x_list = get_axis()
    buttons.LEFT_X = left_x_list[0]
    if left_x_list[1] < 0:
        buttons.LEFT_X_REVERSE = -1

    print(buttons.LEFT_Y)
    print(buttons.LEFT_Y_REVERSE)
    print(buttons.LEFT_X)
    print(buttons.LEFT_X_REVERSE)


def setup_two_joystick():
    print('Push left joystick up')
    left_y_list = get_axis()
    buttons.LEFT_Y = left_y_list[0]
    if left_y_list[1] < 0:
        buttons.LEFT_Y_REVERSE = -1

    print('Push left joystick to the right')
    left_x_list = get_axis()
    buttons.LEFT_X = left_x_list[0]
    if left_x_list[1] < 0:
        buttons.LEFT_X_REVERSE = -1

    print('Push right joystick up')
    right_y_list = get_axis()
    buttons.RIGHT_Y = right_y_list[0]
    if right_y_list[1] < 0:
        buttons.RIGHT_Y_REVERSE = -1

    print('Push right joystick to the right')
    right_x_list = get_axis()
    buttons.RIGHT_X = right_x_list[0]
    if right_x_list[1] < 0:
        buttons.RIGHT_X_REVERSE = -1

    print(buttons.LEFT_Y)
    print(buttons.LEFT_Y_REVERSE)
    print(buttons.LEFT_X)
    print(buttons.LEFT_X_REVERSE)
    print(buttons.RIGHT_Y)
    print(buttons.RIGHT_Y_REVERSE)
    print(buttons.RIGHT_X)
    print(buttons.RIGHT_X_REVERSE)


def get_axis():
    count = 500
    sum = 0
    values = []
    last_val = 0
    time.sleep(1)
    pygame.event.clear()
    pygame.event.wait()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.locals.JOYAXISMOTION:
                if -buttons.DEADZONE <= e.value <= buttons.DEADZONE:
                    e.value = 0
                if e.value != 0:
                    val = abs(e.value)
                    if (val - last_val) > 0:
                        values.append(e.axis)
                        sum = sum + e.value
                        count = count - 1
                        if count < 0:
                            break
                    last_val = val
        if count < 0:
            break
    print('Done')

    max_i = 0
    set_values = set(values)
    print(set_values)
    for value in set_values:
        i = 0
        for item in values:
            if value == item:
                i = i + 1
        if i > max_i:
            max_i = i
            axis = value

    answer = [axis, sum]
    return answer


def set_deadzone():
    print('Please do not press any buttons or touch any joysticks...')
    time.sleep(1)

    max = 0
    count = 1000
    pygame.event.clear()
    pygame.event.wait()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.locals.JOYAXISMOTION:
                if abs(e.value) > max:
                    max = e.value
                count = count - 1
                if count < 0:
                    break
        if count < 0:
            break

    print('Done')
    if abs(max) > .01:
        buttons.DEADZONE = abs(max)


def setup_drone():
    global drone

    drone = tellopy.Tello()
    drone.connect()
    drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
    threading.Thread(target=recv_thread, args=[drone]).start()


def recv_thread(drone):
    global run_recv_thread
    global new_image
    global flight_data
    global current_image

    try:
        container = av.open(drone.get_video_stream())
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
    d = 2
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


def handle_input_event(drone, e):
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
            pitch = update(pitch, e.value *
                           buttons.RIGHT_Y_REVERSE)
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


def handler(event, sender, data, **args):
    global prev_flight_data
    global flight_data
    global drone

    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        #if prev_flight_data != str(data):
        print(data)
        prev_flight_data = str(data)
        flight_data = data
    else:
        print('event="%s" data=%s' % (event.getname(), str(data)))


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