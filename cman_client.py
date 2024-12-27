from cman_utils import *
import socket
import argparse
from cman_game_map import *
from copy import deepcopy
import os
import platform
import time
import threading

fps = 60
frame_duration = 1/fps

CHAR_VISUAL = {WALL_CHAR: "█",
               POINT_CHAR: "*",
               CMAN_CHAR: "☺",
               SPIRIT_CHAR: "@",
               FREE_CHAR: " "}

KEY_TO_DIRECTION = {'W': 0,
                    'A': 1,
                    'S': 2,
                    'D': 3,
                    'w': 0,
                    'a': 1,
                    's': 2,
                    'd': 3}

OPCODES = {"join": 0x00,
           "move": 0x01,
           "quit": 0x0F,
           "game update": 0x80,
           "end": 0x8F,
           "error": 0xFF}

ERRORS = { 0: "ERROR: Wrong opcode sent to server",
           1: "ERROR: No data sent",
           2: "ERROR: Invalid directions",
           3: "ERROR: Incorrect desired role",
           10: "ERROR: Role taken"}

ROLE_TO_CODE = {"watcher": 0,
                "cman": 1,
                "spirit": 2}


def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def print_map(board):
    clear_terminal()
    rows, columns = (len(board), len(board[0]))
    for i in range(rows):
        for j in range(columns):
            print(CHAR_VISUAL[board[i][j]], end='')
        print("")

def load_map(map_path):
    board = read_map(map_path).split('\n')
    board = [list(row) for row in board]
    return board

def get_full_map(board, points, cman_coords, spirit_coords):
    board = deepcopy(board)
    i, j = cman_coords
    board[i][j] = CMAN_CHAR
    i, j = spirit_coords
    board[i][j] = SPIRIT_CHAR
    for coords in points:
        i, j = coords
        board[i][j] = POINT_CHAR
    return board

def strip_map(board):
    board = deepcopy(board)
    rows, columns = (len(board), len(board[0]))
    for i in range(rows):
        for j in range(columns):
            board[i][j] = FREE_CHAR if board[i][j] != WALL_CHAR else WALL_CHAR
    return board


class Map:
    def __init__(self):
        og_map = load_map("map.txt")
        self.attempts = 0
        self.rows = len(og_map)
        self.cols = len(og_map[0])
        self.points_alive = [True]*MAX_POINTS
        self.og_point_positions = [(i, j) for i in range(self.rows) for j in range(self.cols) if
                                og_map[i][j] == POINT_CHAR]
        self.point_positions = deepcopy(self.og_point_positions)
        self.cman_coords = [(i, j) for i in range(self.rows) for j in range(self.cols) if og_map[i][j] == CMAN_CHAR]
        self.cman_coords = self.cman_coords[0]
        self.spirit_coords = [(i, j) for i in range(self.rows) for j in range(self.cols) if og_map[i][j] == SPIRIT_CHAR]
        self.spirit_coords = self.spirit_coords[0]
        self.base_map = strip_map(og_map)
        self.full_map = get_full_map(self.base_map, self.point_positions, self.cman_coords, self.spirit_coords)


    def refresh_map(self):
        self.full_map = get_full_map(self.base_map, self.point_positions, self.cman_coords, self.spirit_coords)

    def refresh_points(self, message: bytearray):
        byte_array = message[7:12]
        for i in range(40):
            byte_index = i // 8
            bit_index = i % 8
            bit = (byte_array[byte_index] >> bit_index) & 1
            self.points_alive[i] = (bit == 0)
        self.point_positions = [self.og_point_positions[i] for i in range(MAX_POINTS) if self.points_alive[i]]
        self.refresh_map()




def get_args():
    parser = argparse.ArgumentParser(description="CMAN Client")
    parser.add_argument("role", type=str, help="The role of the player")
    parser.add_argument("addr", type=str, help="The address of the server")
    parser.add_argument("-p", "--port", type=int, default=1337, help="The port number (default: 1337)")
    args = parser.parse_args()
    return args.role, args.addr, args.port


class Client:
    def __init__(self):
        self.map = Map()
        self.role, addr, port = get_args()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (addr, port)
        self.socket.setblocking(False)
        self.can_move = False
        self.last_key = None

    def join_game(self):
        message = bytearray([OPCODES["join"], ROLE_TO_CODE[self.role]])
        self.socket.sendto(message, self.server_address)

    def handle_error(self, message):
        error_message = ERRORS[message[1]]
        print(error_message)
        self.socket.close()
        exit(1)

    def game_end(self, message):
        _, winner, captures, score = message
        winner = "Cman" if winner == 1 else "Spirit"
        print(f"GAME OVER\n The winner is: {winner}")
        print(f"Cman got captured: {captures} times")
        print(f"Score: {score}")
        self.socket.close()
        exit(0)

    def handle_game_update(self, message):
        self.can_move = message[1] == 0
        self.map.cman_coords = (message[2], message[3])
        self.map.spirit_coords = (message[4], message[5])
        self.map.attempts = message[6]
        self.map.refresh_points(message)
        print_map(self.map.full_map)


    def handle_server_response(self):
        opcode_to_handler = {0x80: self.handle_game_update,
                             0x8F: self.game_end,
                             0xFF: self.handle_error}
        try:
            data, addr = self.socket.recvfrom(1024)
        except BlockingIOError:
            return
        except Exception as e:
            print("Error enocuntered with socket, existing")
            exit(0)

        if addr != self.server_address:
            return
        opcode = data[0]
        if opcode not in opcode_to_handler:
            return #error
        opcode_to_handler[opcode](data)

    def send_move(self, move):
        message = bytearray([OPCODES["move"], move])
        self.socket.sendto(message, self.server_address)

    def send_quit(self):
        message = bytearray([OPCODES["quit"]])
        self.socket.sendto(message, self.server_address)
        self.socket.close()
        exit(0)

    def handle_player_input(self):
        while True:
            pressed = get_pressed_keys()
            for key in pressed:
                if key in KEY_TO_DIRECTION or key == 'Q' or key == 'q':
                    self.last_key = key


    def move(self):
        if not self.can_move:
            return
        key = self.last_key
        self.last_key = None
        if key is not None:
            if key in KEY_TO_DIRECTION:
                self.send_move(KEY_TO_DIRECTION[key])
                return
            if key == 'Q' or key == 'q':
                self.send_quit()

    def run(self):
        self.join_game()
        input_thread =  threading.Thread(target=self.handle_player_input, args=())
        input_thread.daemon = True
        input_thread.start()
        while True:
            start_time = time.time()
            self.handle_server_response()
            self.move()
            elapsed_time = time.time() - start_time
            sleep_time = max(0, frame_duration - elapsed_time)
            time.sleep(sleep_time)



if __name__ == "__main__":
    client = Client()
    client.run()
