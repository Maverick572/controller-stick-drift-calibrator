from joystickUI import UI
import pygame
from joystickMapper import start_mapper, stop_mapper
import sys, os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS  # temp folder PyInstaller extracts to
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def refresh_devices():
    pygame.init()
    pygame.joystick.init()
    return [pygame.joystick.Joystick(i).get_name()
            for i in range(pygame.joystick.get_count())]

# Create UI instance
ui = UI(on_start=start_mapper, on_stop=stop_mapper, on_refresh=refresh_devices)

# Set window properties AFTER creation
ui.app.title("Joystick Calibrator")
ui.app.iconbitmap(resource_path("icon.ico"))

# Run app
ui.run()
