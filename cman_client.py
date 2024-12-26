from cman_utils import *
import socket
import argparse

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


def get_args():
    parser = argparse.ArgumentParser(description="CMAN Client")
    parser.add_argument("role", type=str, help="The role of the player")
    parser.add_argument("addr", type=str, help="The address of the server")
    parser.add_argument("-p", "--port", type=int, default=1337, help="The port number (default: 1337)")
    args = parser.parse_args()
    return args.role, args.addr, args.port


class Client:
    def __init__(self):
        self.role, addr, port = get_args()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        self.server_address = (addr, port)
        self.socket.setblocking(False)

    def join_game(self):
        message = bytearray([OPCODES["join"], ROLE_TO_CODE[self.role]])
        self.socket.sendto(message, self.server_address)

    def handle_error(self, message):
        error_message = ERRORS[message[1]]
        print(error_message)
        self.socket.close()
        exit(1)

    def run(self):
        self.join_game()
        while True:
            data, addr = self.socket.recvfrom(1024)
            if addr != self.server_address:
                continue #Received message not from server
            opcode = data[0]



