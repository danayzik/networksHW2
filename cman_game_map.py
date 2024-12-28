from map_constants import *
from copy import deepcopy
import os
import platform

def read_map(path):
    """

    Reads map data and asserts that it is valid.

    Parameters:

    path (str): path to the textual map file

    """
    with open(path, 'r') as f:
        map_data = f.read()

        map_chars = set(map_data)
        assert map_chars.issubset({CMAN_CHAR, SPIRIT_CHAR, POINT_CHAR, WALL_CHAR, FREE_CHAR, '\n'}), "invalid char in map."
        assert map_data.count(CMAN_CHAR) == 1, "Map needs to have a single C-Man starting point."
        assert map_data.count(SPIRIT_CHAR) == 1, "Map needs to have a single Spirit starting point."
        assert map_data.count(POINT_CHAR) == MAX_POINTS, f"Map needs to have {MAX_POINTS} score points."

        map_lines = map_data.split('\n')
        assert all(len(line) == len(map_lines[0]) for line in map_lines), "map is not square."
        assert len(map_lines) < 2**8, "map is too tall"
        assert len(map_lines[0]) < 2**8, "map is too wide"

        sbc = all(line.startswith(WALL_CHAR) and line.endswith(WALL_CHAR) for line in map_lines)
        tbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        bbc = map_lines[0] == WALL_CHAR*len(map_lines[0]) and map_lines[-1] == WALL_CHAR*len(map_lines[-1])
        assert sbc and tbc and bbc, "map border is open."

        return map_data

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
        self.og_point_positions = [(i, j) for i in range(self.rows)
                                            for j in range(self.cols)
                                        if og_map[i][j] == POINT_CHAR]
        self.point_positions = deepcopy(self.og_point_positions)
        self.cman_coords = [(i, j) for i in range(self.rows) for j in range(self.cols) if og_map[i][j] == CMAN_CHAR]
        self.cman_coords = self.cman_coords[0]
        self.spirit_coords = [(i, j) for i in range(self.rows) for j in range(self.cols) if og_map[i][j] == SPIRIT_CHAR]
        self.spirit_coords = self.spirit_coords[0]
        self.base_map = strip_map(og_map)
        self.full_map = get_full_map(self.base_map, self.point_positions, self.cman_coords, self.spirit_coords)

    def print_map(self):
        print_map(self.full_map)

    def refresh_map(self):
        self.full_map = get_full_map(self.base_map, self.point_positions, self.cman_coords, self.spirit_coords)

    def refresh_points(self, message: bytearray):
        byte_array = message[7:12]
        for i in range(40):
            byte_index = i // 8
            bit_index = 7 - i % 8
            bit = (byte_array[byte_index] >> bit_index) & 1
            self.points_alive[i] = (bit == 0)
        self.point_positions = [self.og_point_positions[i] for i in range(MAX_POINTS) if self.points_alive[i]]
        self.refresh_map()
