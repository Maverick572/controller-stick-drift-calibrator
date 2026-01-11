from joystickUI import UI
import sys
import os
import pygame
import ctypes

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "com.yourname.joystickcalibrator"
)

# ───────────────────────────── ViGEm Check ───────────────────────────── #
def check_vigem():
    try:
        import vgamepad
        vgamepad.VX360Gamepad()
        return True
    except Exception:
        ctypes.windll.user32.MessageBoxW(
            None,
            "ViGEmBus driver is not installed.\n\n"
            "This application requires ViGEmBus to create virtual controllers.\n\n"
            "Please run 'ViGEmBus_Setup.exe' included with this app,\n"
            "then restart the application.\n\n"
            "Administrator privileges are required for installation.",
            "Missing Dependency",
            0x10  # MB_ICONERROR
        )
        return False

if not check_vigem():
    sys.exit(1)

# ───────────────────────────── Resources ───────────────────────────── #
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ───────────────────────────── Pygame Init ───────────────────────────── #
pygame.init()
pygame.joystick.init()

# ───────────────────────────── Device Refresh ───────────────────────────── #
def refresh_devices():
    names = []
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        names.append(js.get_name())
    return names

# ───────────────────────────── App Startup ───────────────────────────── #
ui = UI(on_refresh=refresh_devices)
ui.run()
