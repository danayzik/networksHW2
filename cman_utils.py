import pynput

class KeyInputHandler:
    def __init__(self):
        self.pressed_keys = []
        self.listener = pynput.keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            if key.char not in self.pressed_keys:
                self.pressed_keys.append(key.char)
        except AttributeError:
            if str(key) not in self.pressed_keys:
                self.pressed_keys.append(str(key))

    def get_pressed_keys(self, keys_filter=None):
        # Return filtered keys or all pressed keys if no filter is provided
        if keys_filter is None:
            return self.pressed_keys
        else:
            return [key for key in self.pressed_keys if key in keys_filter]

    def clear_pressed_keys(self):
        # Clear the list of pressed keys after processing
        self.pressed_keys = []

    def stop_listener(self):
        # Stop the listener (you can call this when the game ends or at the right time)
        self.listener.stop()