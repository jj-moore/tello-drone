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
current_user = None


class User:
    name = ''
    type = ''
    organization = ''
    major = ''

    def __str__(self):
        return f'Name: {self.name} Type: {self.type} Org: {self.organization} Major: {self.major}'


class JoystickPS3:
    QUIT = 10

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
    RIGHT_X = 3
    RIGHT_Y = 4
    LEFT_X_REVERSE = 1.0
    LEFT_Y_REVERSE = -1.0
    RIGHT_X_REVERSE = 1.0
    RIGHT_Y_REVERSE = -1.0
    DEADZONE = 0.01


class JoystickPS4:
    QUIT = 10

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


class JoystickPS4ALT:
    QUIT = -1

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
    QUIT = -1
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
    QUIT = 10

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
    RIGHT_X = 3
    RIGHT_Y = 4
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
    global current_user
    num_args = len(sys.argv)
    current_user = User()
    if num_args > 1:
        current_user.name = sys.argv[1]
    if num_args > 2:
        current_user.type = sys.argv[2]
    if num_args > 3:
        current_user.organization = sys.argv[3]
    if num_args > 4:
        current_user.major = sys.argv[4]
    print(f' Hello {current_user.name}!')
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
            buttons = JoystickPS4
        elif js_name == 'Sony Interactive Entertainment Wireless Controller':
            buttons = JoystickPS4ALT
        elif js_name in ('PLAYSTATION(R)3 Controller', 'Sony PLAYSTATION(R)3 Controller'):
            buttons = JoystickPS3
        elif js_name in 'Logitech Gamepad F310':
            buttons = JoystickF310
        elif js_name in ('Xbox One Wired Controller', 'Microsoft X-Box One pad'):
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

    number_of_joystick = js.get_numaxes()
    if number_of_joystick != 0:
        print('Time to set up the joystick(s) if at any point you decide to not set up a joystick just press'
              'the Takeoff button.')
    if number_of_joystick >= 4:
        setup_two_joystick()
    elif number_of_joystick != 0:
        setup_one_joystick()


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
    print('Push joystick back and forth between center and up.')
    left_y_list = get_axis()
    buttons.LEFT_Y = left_y_list[0]
    if left_y_list[1] < 0:
        buttons.LEFT_Y_REVERSE = -1
    if buttons.LEFT_Y is None:
        return

    print('Push joystick back and forth between center and to the right')
    left_x_list = get_axis()
    buttons.LEFT_X = left_x_list[0]
    if left_x_list[1] < 0:
        buttons.LEFT_X_REVERSE = -1
    if buttons.LEFT_X is None:
        return


def setup_two_joystick():
    print('Push left joystick back and forth between center and up')
    left_y_list = get_axis()
    buttons.LEFT_Y = left_y_list[0]
    if left_y_list[1] < 0:
        buttons.LEFT_Y_REVERSE = -1
    if buttons.LEFT_Y is None:
        return

    print('Push left joystick back and forth between center and to the right')
    left_x_list = get_axis()
    buttons.LEFT_X = left_x_list[0]
    if left_x_list[1] < 0:
        buttons.LEFT_X_REVERSE = -1
    if buttons.LEFT_X is None:
        return

    print('Push right joystick back and forth between center and up')
    right_y_list = get_axis()
    buttons.RIGHT_Y = right_y_list[0]
    if right_y_list[1] < 0:
        buttons.RIGHT_Y_REVERSE = -1
    if buttons.RIGHT_Y is None:
        return

    print('Push right joystick back and forth between center to the right')
    right_x_list = get_axis()
    buttons.RIGHT_X = right_x_list[0]
    if right_x_list[1] < 0:
        buttons.RIGHT_X_REVERSE = -1
    if buttons.RIGHT_X is None:
        return


def get_axis():
    my_stop = False
    count = 500
    my_sum = 0
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
                        my_sum = my_sum + e.value
                        count = count - 1
                        if count < 0:
                            break
                    last_val = val
            elif e.type == pygame.locals.JOYBUTTONDOWN:
                if e.button == buttons.TAKEOFF:
                    my_stop = True
        if count < 0 or my_stop:
            break
    print('Done')

    if my_stop:
        return [None, 1]

    max_i = 0
    set_values = set(values)
    axis = None
    for value in set_values:
        i = 0
        for item in values:
            if value == item:
                i = i + 1
        if i > max_i:
            max_i = i
            axis = value

    answer = [axis, my_sum]
    return answer


def set_deadzone():
    print('Please do not press any buttons or touch any joysticks...')
    time.sleep(1)

    my_max = 0
    count = 1000
    pygame.event.clear()
    pygame.event.wait()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.locals.JOYAXISMOTION:
                if abs(e.value) > my_max:
                    my_max = abs(e.value)
                count = count - 1
                if count < 0:
                    break
        if count < 0:
            break

    print('Done')
    if my_max > .01:
        buttons.DEADZONE = my_max


def setup_drone():
    global drone
    drone = tellopy.Tello()
    drone.connect()
    drone.subscribe(drone.EVENT_FLIGHT_DATA, flight_data_handler)
    drone.subscribe(drone.EVENT_LOG_DATA, log_data_handler)
    threading.Thread(target=recv_thread, args=[drone]).start()


def recv_thread(my_drone):
    global run_recv_thread
    global new_image
    global flight_data
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
    print(f'X:{data.mvo.pos_x} Y:{data.mvo.pos_y} Z:{data.mvo.pos_z} {current_user}')


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
