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

# custom files
import classes

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

    buttons = classes.CustomController(control_set)
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
