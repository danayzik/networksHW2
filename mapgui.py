import tkinter as tk

class MapGUI:
    def __init__(self, map_data):
        self.root = tk.Tk()
        self.root.title("C-Man")
        self.map_data = map_data
        self.labels = []

        for i, row in enumerate(map_data):
            label_row = []
            for j, char in enumerate(row):
                label = tk.Label(self.root, text=char, font=("Courier", 16), width=2, height=1)
                label.grid(row=i, column=j)
                label_row.append(label)
            self.labels.append(label_row)

    def update_map(self, map_data):
        self.map_data = map_data
        for i, row in enumerate(map_data):
            for j, char in enumerate(row):
                self.labels[i][j].config(text=char)

    def run(self):
        self.root.mainloop()

# Example usage:
if __name__ == "__main__":
    # Initial map data
    example_map = [
        "########",
        "#......#",
        "#.C....#",
        "#......#",
        "#...S..#",
        "########",
    ]
    gui = MapGUI([list(row) for row in example_map])

    # Simulate a map update after 2 seconds
    def simulate_update():
        new_map = [
            "########",
            "#......#",
            "#......#",
            "#.C....#",
            "#...S..#",
            "########",
        ]
        gui.update_map([list(row) for row in new_map])

    gui.root.after(2000, simulate_update)  # Update map after 2 seconds
    gui.run()
