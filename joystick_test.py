import time
import pygame
import pygame.locals


def handle_input_event(event):
	# ignore non-joystick events
	if event.type < pygame.locals.JOYAXISMOTION or event.type > pygame.locals.JOYBUTTONUP:
		return

	# ignore joystick axis events within the deadzone
	if event.type == pygame.locals.JOYAXISMOTION:
		if -DEADZONE <= event.value <= DEADZONE:
			return

	event_properties = event.__dict__
	event_type = convert_int_to_pygame_event_type(event.type)
	event_properties['event'] = event_type

	# print all properties of the event object
	print(event_properties)


def convert_int_to_pygame_event_type(event_num):
	if event_num == 7:
		return 'JOYAXISMOTION'
	if event_num == 8:
		return 'JOYBALLMOTION'
	if event_num == 9:
		return 'JOYHATMOTION'
	if event_num == 10:
		return 'JOYBUTTONUP'
	if event_num == 11:
		return 'JOYBUTTONDOWN'


pygame.init()
pygame.joystick.init()
count = pygame.joystick.get_count()
print(f'You have {count} joysticks reporting')
DEADZONE = 0.2

# if at least one joystick present, handle events of the first joystick
if count > 0:
	joystick = pygame.joystick.Joystick(0)
	joystick.init()
	print(f'Joystick Name: {joystick.get_name()}')
	while 1:
		time.sleep(0.1)
		for e in pygame.event.get():
			handle_input_event(e)
