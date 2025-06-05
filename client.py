import socket
import threading
import sys

from PyQt6 import QtWidgets

from game_screen import Ui_GameWindow
from welcome import Ui_MainWindow
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
from PyQt6.QtCore import QTimer


class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = None

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))

    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(message.encode())

    def recv_message(self):
        return self.client_socket.recv(1024).decode()

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()


def handle_game_over(result):
    print(result)


def handle_turn_start(window, letters):
    window.clear_input()
    window.update_info_text(letters)
    window.update_status("🎯 Your Turn!", "cyan")
    print(f"Your turn! Your letters: {letters}")
    window.set_input_enabled(True)
    window.input_box.setFocus()


def handle_update_input(window, others_inputs):
    window.display_inputs_of_other_clients(others_inputs)


def handle_update_letters(window, others_inputs):
    window.update_info_text(others_inputs)


def handle_valid_word(window):
    print("Valid word! Turn over.")
    window.set_input_enabled(False)
    window.update_status("✅ Valid Word!", "green")


def handle_time_up(window):
    print(f"Time's up! you lose 1 life.")
    window.set_input_enabled(False)
    window.clear_input()
    window.update_status("⏰ Time's Up!", "orange")


def handle_life_lost(window, value):
    try:
        name, hearts_str = value.split(":")
        hearts = int(hearts_str)
        window.update_hearts(name, hearts)
        print(f"**********{hearts},{name}")
    except Exception as e:
        print(f"Failed to parse life lost message: {value} — {e}")


def handle_invalid_word(window, retry_message):
    print(retry_message)
    window.update_status("❌ Invalid Word, try again!", "red")


def handle_used_word(window, retry_message):
    print(retry_message)
    window.update_status("©️ Used Word, try again!", "red")


def handle_player_list(window, player_list_str):
    names = player_list_str.split(",")
    window.update_player_list(names)


def handle_admin(window, value):
    if value == "GAME_STARTED":
        window.start_button.setEnabled(False)  # enable the button
        window.start_button.hide()  # show the button
    elif value == "YOU_ARE_THE_HOST":
        window.start_button.setEnabled(True)  # enable the button


def handle_server_messages(client, window):
    try:
        message_handlers = {
            "ADMIN": lambda values: handle_admin(window, values),
            "GAME_OVER": lambda values: handle_game_over(values),
            "TURN_START": lambda values: handle_turn_start(window, values),
            "UPDATE_INPUT": lambda values: handle_update_input(window, values),
            "UPDATE_LETTERS": lambda values: handle_update_letters(window, values),
            "VALID_WORD": lambda values: handle_valid_word(window),
            "TIME_UP": lambda values: handle_time_up(window),
            "PLAYER_LOST_LIFE": lambda values: handle_life_lost(window, values),
            "INVALID_WORD": lambda values: handle_invalid_word(window, values),
            "USED_WORD": lambda values: handle_used_word(window, values),
            "PLAYER_LIST": lambda values: handle_player_list(window, values)

        }

        while True:
            data = client.recv_message()
            print(f"got from server: {data}")
            data_list = data.split("\n")
            for message in data_list:
                if message != "":
                    parts = message.split("|")
                    command, value = parts[0], parts[1] if len(parts) > 1 else []
                    if command in message_handlers:
                        message_handlers[command](value)
                    else:
                        print(f"Unknown message: {message}")

    except Exception as e:
        print(f"Error in server message handler: {e}")
        client.close_connection()


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setupUi(self)
        self.pushButton.clicked.connect(self.click_handler)

    def click_handler(self):
        entered_name = self.lineEdit.text().strip()
        if entered_name:
            self.client.send_message(entered_name)  # Send the name to the server
            # Open GameWindow
            self.game_window = GameWindow(self.client)
            threading.Thread(target=handle_server_messages, args=(self.client, self.game_window), daemon=True).start()
            self.game_window.show()
            self.close()  # Close welcome screen


class GameWindow(QMainWindow, Ui_GameWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.displayed_players = set()
        self.saved_text = ""
        self.player_hearts = {}  # maps player name -> QLabel showing their hearts
        self.setupUi(self)

        # Connect UI events
        self.input_box.textChanged.connect(self.save_input)
        self.input_box.returnPressed.connect(self.send_input)
        self.input_box.setEnabled(False)
        self.start_button.clicked.connect(self.start_game)
        self.start_button.setEnabled(False)

    def update_player_list(self, player_names):
        self._player_names_to_update = player_names
        QTimer.singleShot(0, self._apply_player_list_update)

    def _apply_player_list_update(self):
        self.clear_player_list()
        self.player_hearts.clear()

        for name in self._player_names_to_update:
            container = QWidget()
            layout = QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(name)
            name_label.setStyleSheet("""
                color: white;
                font-weight: bold;
                font-size: 16px;
            """)

            hearts_label = QLabel("❤️❤️❤️")  # Default 3 lives
            hearts_label.setStyleSheet("font-size: 16px; margin-left: 10px;")

            layout.addWidget(name_label)
            layout.addWidget(hearts_label)

            self.player_list_layout.addWidget(container)

            self.displayed_players.add(name)
            self.player_hearts[name] = hearts_label  # Store for future updates

    def update_hearts(self, name, hearts):
        if name in self.displayed_players:
            print("saasdsfsdff")
            self.player_hearts[name].setText("❤️" * hearts)

    def clear_player_list(self):
        while self.player_list_layout.count():
            item = self.player_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def update_info_text(self, text):
        self.letters_label.setText(text)

    def update_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")

    def set_input_enabled(self, state: bool):
        self.input_box.setDisabled(not state)

    def display_inputs_of_other_clients(self, client_inputs):
        self.input_box.setText(client_inputs)

    def save_input(self, text):
        self.saved_text = text
        print(f"text entered {text}")
        self.client.send_message(f"INPUT_CLIENT|{text}\n")

    def send_input(self):
        self.client.send_message("INPUT_CLIENT|ENTER\n")
        self.clear_input()

    def clear_input(self):
        self.input_box.clear()
        self.saved_text = ""

    def start_game(self):
        print("startButton pressed")
        self.client.send_message("BUTTON|START_GAME\n")


# --- main function ---
def main():
    ip = '127.0.0.1'
    port = 65432
    app = QApplication([])

    client = Client(ip, port)
    client.connect_to_server()
    window = Window(client)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
