import sys
import traceback
import tellopy
import av
import cv2.cv2 as cv2  # for avoidance of pylint error
import numpy
import pygame
import pygame.locals
import pygame.key
import threading
import time

# custom files
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
show_video = False

flight_data = None  # log data
drone = None  # Tellopy object


#  Command line entry point
def main():
    initialize_joystick()
    initialize_drone()
    run()


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
    threading.Thread(target=video_thread).start()


def run():
    global new_image
    global current_image

    try:
        while 1:
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


#  command line stop
def stop():
    global show_video
    show_video = False
    cv2.destroyAllWindows()
    drone.quit()
    exit(1)


def video_thread():
    global new_image
    global show_video
    print('start video_thread()')
    show_video = True
    try:
        container = av.open(drone.get_video_stream())
        # skip first 300 frames
        frame_skip = 300
        while show_video:
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


def flight_data_handler(event, sender, data, **args):
    global flight_data
    flight_data = data


def log_data_handler(event, sender, data, **args):
    print(data)


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
