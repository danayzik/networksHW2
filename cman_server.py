#!/usr/bin/python3
import socket
import argparse
from typing import Optional
from cman_game import Game

OPCODES = {"join": 0x00,
           "move": 0x01,
           "quit": 0x0F,
           "game update": 0x80,
           "end": 0x8F,
           "error": 0xFF}

ROLES = {0 : "spectator", 1: "Cman", 2: "Spirit"}

def read_script_inputs() -> int:
    parser = argparse.ArgumentParser(description="Run the server script.")
    parser.add_argument("-p", "--port", type=int, default=1337,
                        help="Specify the port to run the server on (default: 1337).")
    args = parser.parse_args()
    return args.port

class ServerClient:
    def __init__(self, address: tuple[str, int], role: int) -> None:
        self.address = address
        self.role = role

    def __hash__(self):
        return hash(self.address)

    def __eq__(self, other: "ServerClient"):
        return self.address == other.address


class Server:
    def __init__(self) -> None:
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = read_script_inputs()
        self.server_address = ("127.0.0.1", self.port)
        self.udp_socket.bind(self.server_address)
        self.cman_player:Optional[ServerClient] = None
        self.spirit_player:Optional[ServerClient] = None
        self.spectators: list[ServerClient] = []
        self.game = Game("map.txt")
        self.clients = set({})

    def handle_new_client(self, data: bytes, client_address: tuple[str, int]) -> None:
        opcode = data[0]
        if hex(opcode) == OPCODES["join"]:
            desired_role = data[1]
            if desired_role == 0:
                client = ServerClient(client_address, desired_role)
                self.clients.add(client)
                self.spectators.append(client)
            elif desired_role == 1:
                if self.cman_player is None:
                    client = ServerClient(client_address, desired_role)
                    self.cman_player = client
                else:
                    pass  # Send error, role already taken
            elif desired_role == 2:
                if self.spirit_player is None:
                    client = ServerClient(client_address, desired_role)
                    self.spirit_player = client
                else:
                    pass  # Send error, role already taken
            else:
                pass  # incorrect desired role, send error

        else:
            pass  # wrong opcode for new client send client an error probably


    def main_loop(self):
        while True:
            data, client_address = self.udp_socket.recvfrom(1024)
            if client_address in self.clients:
                pass
            else:
                self.handle_new_client(data, client_address)








