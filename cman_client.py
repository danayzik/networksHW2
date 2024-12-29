#!/usr/bin/python3
from typing import Optional
from cman_utils import KeyInputHandler
import socket
import argparse
import select
from cman_game_map import Map
import time
import threading
from constants import OPCODES, ROLE_TO_CODE, ERRORS, KEY_TO_DIRECTION



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
        self.key_handler = KeyInputHandler()
        self.role, addr, port = get_args()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (addr, port)
        self.can_move = False
        self.last_key = None

        self.last_update_message: Optional[bytearray] = None

    def join_game(self):
        print(f"Will try to join as {self.role}")
        if self.role == "watcher":
            print("You will not be able to move")
        message = bytearray([OPCODES["join"], ROLE_TO_CODE[self.role]])
        self.socket.sendto(message, self.server_address)
        print("Sent join request, waiting for players")
        print("Map will load when game starts")

    def handle_error(self, message):
        error_message = ERRORS[message[1]]
        print(error_message)
        self.socket.close()
        exit(1)

    def game_end(self, message):
        _, winner, captures, score = message
        winner = "Cman" if winner == 1 else "Spirit"
        print(f"GAME OVER\nThe winner is: {winner}")
        print(f"Cman got captured: {captures} times")
        print(f"Score: {score}")
        self.socket.close()
        exit(0)


    def handle_game_update(self, message):
        if message != self.last_update_message:
            self.last_update_message = message
            self.can_move = message[1] == 0
            self.map.cman_coords = (message[2], message[3])
            self.map.spirit_coords = (message[4], message[5])
            self.map.attempts = message[6]
            self.map.refresh_points(message)
            self.map.print_map()
            print(f"Number of times cman was caught: {self.map.attempts}")
            if self.role == "watcher":
                print("Spectator mode")


    def handle_server_response(self):
        opcode_to_handler = {0x80: self.handle_game_update,
                             0x8F: self.game_end,
                             0xFF: self.handle_error}
        opcode_length = {0x80: 11,
                             0x8F: 3,
                             0xFF: 1}
        readable, _, _ = select.select([self.socket], [], [], 0.01)
        self.move()
        if readable:
            data, addr = self.socket.recvfrom(1024)
            i = 0
            while i < len(data):
                opcode = data[i]
                i += 1
                command = data[i:i + opcode_length[opcode]]
                i += opcode_length[opcode]
                if opcode not in opcode_to_handler:
                    return  # error
                opcode_to_handler[opcode](bytearray([opcode]) + command)
                self.move()


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
            pressed_keys = self.key_handler.get_pressed_keys()
            for key in pressed_keys:
                if key in KEY_TO_DIRECTION or key == 'Q' or key == 'q':
                    self.last_key = key
                    self.key_handler.clear_pressed_keys()
                    time.sleep(0.05)
                    continue



    def move(self):
        key = self.last_key
        self.last_key = None
        if key is not None:
            if key in KEY_TO_DIRECTION:
                if not self.can_move:
                    return
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
            self.handle_server_response()





if __name__ == "__main__":
    client = Client()
    try:
        client.run()
    except KeyboardInterrupt:
        client.send_quit()