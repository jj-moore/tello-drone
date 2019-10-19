import pygame
import pygame.locals
import time

reset = False
buttons = None


def main(js):
    global reset
    print('No supported controller found, initializing custom controller.')

    while True:
        new_controller(js)
        if not reset:
            break
        reset = False

    return buttons


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


def get_input():
    pygame.event.clear()
    pygame.event.wait()
    while True:
        for e in pygame.event.get():
            # if abs(e.value) > .1:
            #      print(e.axis)
            if e.type == pygame.locals.JOYBUTTONDOWN:
                return e.button


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
