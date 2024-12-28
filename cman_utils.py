import pynput

class KeyInputHandler:
    def __init__(self):
        self.pressed_keys = []
        self.listener = pynput.keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:

            self.pressed_keys.append(key.char)
        except AttributeError:

            self.pressed_keys.append(str(key))

    def get_pressed_keys(self):
        # Return filtered keys or all pressed keys if no filter is provided
        return self.pressed_keys

    def clear_pressed_keys(self):
        # Clear the list of pressed keys after processing
        self.pressed_keys = []

    def stop_listener(self):
        # Stop the listener (you can call this when the game ends or at the right time)
        self.listener.stop()