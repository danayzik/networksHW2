FPS = 2


OPCODES = {"join": 0x00,
           "move": 0x01,
           "quit": 0x0F,
           "game update": 0x80,
           "end": 0x8F,
           "error": 0xFF}


KEY_TO_DIRECTION = {'W': 0,
                    'A': 1,
                    'S': 2,
                    'D': 3,
                    'w': 0,
                    'a': 1,
                    's': 2,
                    'd': 3}

ERRORS = { 0: "ERROR: Wrong opcode sent to server",
           1: "ERROR: No data sent",
           2: "ERROR: Invalid directions",
           3: "ERROR: Incorrect desired role",
           10: "ERROR: Role taken"}

ROLE_TO_CODE = {"watcher": 0,
                "cman": 1,
                "spirit": 2}

frame_duration = 1 / FPS