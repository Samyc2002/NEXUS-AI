import os
import sys
import time
import yaml

config_file_path = "E:\\Projects\\NEXUS Main\\NEXUS AI\\config.yaml"


def load_config():
    """
    The `load_config` function reads a YAML configuration file and sets the values as environment
    variables in Python.
    """
    with open(config_file_path) as config_file:
        config = yaml.safe_load(config_file)
        for key in config.keys():
            os.environ[key] = str(config[key])


def listen_to_keyboard(exit_event):
    """
    The `listen_to_keyboard` function in Python allows for detecting keyboard input to listen for the
    "q" key and set an exit event accordingly, with platform-specific implementations for Windows and
    POSIX systems.

    :param exit_event: The `exit_event` parameter is a threading.Event object that is used to signal
    when the program should exit based on keyboard input. When the "q" key is pressed, the `exit_event`
    will be set, indicating that the program should stop listening to the keyboard input and exit
    gracefully
    :return: The `listen_to_keyboard` function returns a nested function `listen` that allows for
    keyboard input detection to listen for the "q" key and set an exit event accordingly. The function
    has platform-specific implementations for Windows and POSIX systems.
    """
    def listen():
        """
        The `listen` function in Python allows for keyboard input detection to listen for the "q" key
        and set an exit event accordingly, with platform-specific implementations for Windows and POSIX
        systems.
        """
        try:
            # ---------- Windows ----------
            import msvcrt
            while not exit_event.is_set():
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in (b"q", b"Q"):
                        exit_event.set()
                        break
                time.sleep(0.05)  # tiny sleep to prevent 100% CPU
        except ImportError:
            # ---------- POSIX (Linux / macOS) ----------
            import termios
            import tty
            import select

            fd = sys.stdin.fileno()
            old_attr = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)                    # raw-ish mode
                while not exit_event.is_set():
                    # select() with a short timeout – non-blocking
                    ready, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if ready:
                        ch = sys.stdin.read(1)
                        if ch.lower() == "q":
                            exit_event.set()
                            break
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_attr)
    print("Terminating NEXUS forcefully.")
    return listen
