import pygame
pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0)
js.init()
print("Press any button (Ctrl+C to quit):")
while True:
    pygame.event.pump()
    for i in range(js.get_numbuttons()):
        if js.get_button(i):
            print("Button pressed:", i)