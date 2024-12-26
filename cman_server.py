#!/usr/bin/python3
import socket
import argparse
from typing import Optional
from cman_game import Game, MAX_ATTEMPTS, Player

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
        print("Server started")
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = read_script_inputs()
        self.server_address = ("127.0.0.1", self.port)
        self.udp_socket.bind(self.server_address)
        self.udp_socket.setblocking(False)
        self.cman_player:Optional[ServerClient] = None
        self.spirit_player:Optional[ServerClient] = None
        self.spectators: list[ServerClient] = []
        self.game = Game("map.txt")
        self.clients = {}


    def handle_new_client(self, data: bytes, client_address: tuple[str, int]) -> None:
        opcode = data[0]
        message = bytearray([OPCODES["error"]])
        if hex(opcode) == OPCODES["join"]:
            desired_role = data[1]
            if desired_role == 0:
                client = ServerClient(client_address, desired_role)
                self.clients[client_address] = client
                self.spectators.append(client)
            elif desired_role == 1:
                if self.cman_player is None:
                    client = ServerClient(client_address, desired_role)
                    self.cman_player = client
                else: # role taken
                    message.append(10)
                    self.udp_socket.sendto(message, client_address)
            elif desired_role == 2:
                if self.spirit_player is None:
                    client = ServerClient(client_address, desired_role)
                    self.spirit_player = client
                else: # role taken
                    message.append(10)
                    self.udp_socket.sendto(message, client_address)
            else: # incorrect desired role
                message.append(3)
                self.udp_socket.sendto(message, client_address)


        else: # wrong opcode for new client
            message.append(0)
            self.udp_socket.sendto(message, client_address)


    def is_game_over(self) -> bool:
        winner = self.game.get_winner()
        return winner != -1

    def append_points_as_bits(self, message: bytearray):
        points_dict = self.game.points
        bit_values = []
        for key, value in points_dict.items():
            bit_values.append(1 - value)
        for i in range(0, 40, 8):
            byte_value = 0
            for j in range(8):
                if i + j < 40:
                    byte_value |= (bit_values[i + j] << (7 - j))
            message.append(byte_value)

    def append_game_state_to_message(self, message: bytearray):
        coords = self.game.get_current_players_coords()
        for player_coords in coords:
            message.append(player_coords[0])
            message.append(player_coords[1])
        attempts = MAX_ATTEMPTS - self.game.get_game_progress()[0]
        message.append(attempts)
        self.append_points_as_bits(message)

    def send_message_to_spectators(self, message: bytearray):
        for spectator in self.spectators:
            address = spectator.address
            self.udp_socket.sendto(message, address)

    def send_message_to_players(self, message: bytearray):
        if self.cman_player is not None:
            self.udp_socket.sendto(message, self.cman_player.address)
        if self.spirit_player is not None:
            self.udp_socket.sendto(message, self.spirit_player.address)

    def finish_game(self):
        winner = self.game.get_winner() + 1
        lives, score = self.game.get_game_progress()
        captures = MAX_ATTEMPTS - lives
        message = bytearray([OPCODES["end"], winner, captures, score])
        self.send_message_to_players(message)
        self.send_message_to_spectators(message)
        self.udp_socket.close()
        exit(1)

    def send_game_updates(self) -> None:
        cman_address = self.cman_player.address
        spirit_address = self.spirit_player.address
        message = bytearray()
        message.append(OPCODES["game update"])
        can_move = self.game.can_move(self.cman_player.role - 1)
        message.append(int(not can_move))
        self.append_game_state_to_message(message)
        self.udp_socket.sendto(message, cman_address)
        can_move = self.game.can_move(self.spirit_player.role - 1)
        message[1] = int(not can_move)
        self.udp_socket.sendto(message, spirit_address)
        message[1] = 1
        self.send_message_to_spectators(message)
        if self.is_game_over():
            self.finish_game()

    def handle_quit(self, client_address: tuple[str, int], data=None) -> None:
        client = self.clients.pop(client_address)
        if client.role == 0:
            self.spectators.remove(client)
            return
        elif client.role == 1:
            self.cman_player = None
            winner = Player.SPIRIT

        else:
            self.spirit_player = None
            winner = Player.CMAN
        self.game.declare_winner(winner)
        self.finish_game()

    def handle_movement(self, client_address: tuple[str, int], data: bytes):
        message = bytearray([OPCODES["error"]])
        client = self.clients[client_address]
        valid_directions = {0, 1, 2, 3}
        player = client.role - 1

        if len(data) == 0:
            message.append(1)
            self.udp_socket.sendto(message, client_address)
            return

        direction = data[1]
        if direction not in valid_directions:
            message.append(2)
            self.udp_socket.sendto(message, client_address)
            return

        if self.game.apply_move(player, direction):
                self.send_game_updates()


    def run(self):
        opcode_to_handler = {0x01: self.handle_movement,
                             0x0F: self.handle_quit}
        while True:
            data, client_address = self.udp_socket.recvfrom(1024)

            if client_address in self.clients:
                opcode = data[0]
                if opcode in opcode_to_handler:
                    opcode_to_handler[opcode](client_address, data)
                else:
                    message = bytearray([OPCODES["error"], 0])
                    self.udp_socket.sendto(message, client_address)
            else:
                self.handle_new_client(data, client_address)



if __name__ == "__main__":
    server = Server()
    server.run()
