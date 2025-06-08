import socket
import threading
import sys
from encryption_manager import EncryptionManager
from PyQt6 import QtWidgets

from game_screen import Ui_GameWindow
from welcome import Ui_MainWindow
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
from PyQt6.QtCore import QTimer, Qt

class MessageHandler:
    @staticmethod
    def handle_game_over(window, result):
        window.show_game_over(result)
        print(result)

    @staticmethod
    def handle_turn_start(window, letters):
        window.clear_input()
        window.update_info_text(letters)
        window.update_status("🎯 Your Turn!", "cyan")
        window.input_box.setPlaceholderText("הכנס מילה כאן")
        window.set_input_enabled(True)
        window.input_box.setFocus()

    @staticmethod
    def handle_update_input(window, others_inputs):
        window.display_inputs_of_other_clients(others_inputs)

    @staticmethod
    def handle_update_letters(window, others_inputs):
        window.update_info_text(others_inputs)

    @staticmethod
    def handle_valid_word(window):
        window.set_input_enabled(False)
        window.update_status("✅ Valid Word!", "green")
        window.clear_input()
        window.input_box.setPlaceholderText("")

    @staticmethod
    def handle_time_up(window):
        window.set_input_enabled(False)
        window.clear_input()
        window.update_status("⏰ Time's Up!", "orange")
        window.input_box.setPlaceholderText("")

    @staticmethod
    def handle_life_lost(window, value):
        try:
            name, hearts_str = value.split(":")
            hearts = int(hearts_str)
            window.update_hearts(name, hearts)
            print(f"**********{hearts},{name}")
        except Exception as e:
            print(f"Failed to parse life lost message: {value} — {e}")

    @staticmethod
    def handle_invalid_word(window, retry_message):
        window.clear_input()
        window.update_status("❌ Invalid Word, try again!", "red")

    @staticmethod
    def handle_used_word(window, retry_message):
        window.update_status("©️ Used Word, try again!", "red")

    @staticmethod
    def handle_player_list(window, player_list_str):
        names = player_list_str.split(",")
        window.update_player_list(names)

    @staticmethod
    def handle_admin(window, value):
        lives = 3  # update to be able to choose
        value, player_list_str = value.split(":")
        player_names = player_list_str.split(",")
        if value == "GAME_STARTED":
            window.start_button.setEnabled(False)  # enable the button
            window.start_button.hide()  # show the button
            window.fill_players_hearts(player_names, lives)
        elif value == "YOU_ARE_THE_HOST":
            window.start_button.setEnabled(True)  # enable the button

def handle_server_messages(client, window):
    try:
        message_handlers = {
            "ADMIN": lambda values: MessageHandler.handle_admin(window, values),
            "GAME_OVER": lambda values: MessageHandler.handle_game_over(window, values),
            "TURN_START": lambda values: MessageHandler.handle_turn_start(window, values),
            "UPDATE_INPUT": lambda values: MessageHandler.handle_update_input(window, values),
            "UPDATE_LETTERS": lambda values: MessageHandler.handle_update_letters(window, values),
            "VALID_WORD": lambda values: MessageHandler.handle_valid_word(window),
            "TIME_UP": lambda values: MessageHandler.handle_time_up(window),
            "PLAYER_LOST_LIFE": lambda values: MessageHandler.handle_life_lost(window, values),
            "INVALID_WORD": lambda values: MessageHandler.handle_invalid_word(window, values),
            "USED_WORD": lambda values: MessageHandler.handle_used_word(window, values),
            "PLAYER_LIST": lambda values: MessageHandler.handle_player_list(window, values)

        }

        while True:
            data = client.recv_message()
            if data.split('|')[0] != "UPDATE_INPUT":
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


class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = None
        self.encryption_manager = EncryptionManager()

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))

        # 1. קבל את המפתח הציבורי מהשרת
        key_length_bytes = self.client_socket.recv(4)
        if len(key_length_bytes) < 4:
            raise ConnectionError("Failed to receive public key length")
        key_length = int.from_bytes(key_length_bytes, 'big')

        public_key_bytes = b""
        while len(public_key_bytes) < key_length:
            chunk = self.client_socket.recv(key_length - len(public_key_bytes))
            if not chunk:
                raise ConnectionError("Connection lost while receiving public key")
            public_key_bytes += chunk

        # טען את המפתח הציבורי
        self.encryption_manager.load_public_key(public_key_bytes)

    def send_encrypted_message(self, message: str):
        encrypted_message = self.encryption_manager.encrypt(message)

        # שלח קודם את אורך ההודעה המוצפנת (4 בייטים)
        self.client_socket.sendall(len(encrypted_message).to_bytes(4, 'big') + encrypted_message)

    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(message.encode())

    def recv_message(self):
        return self.client_socket.recv(1024).decode()

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setupUi(self)
        self.pushButton.clicked.connect(self.click_handler)

    def click_handler(self):
        entered_name = self.lineEdit.text().strip()
        if entered_name:
            self.client.send_encrypted_message(entered_name)  # Send the name to the server
            # Open GameWindow
            self.game_window = GameWindow(self.client)
            threading.Thread(target=handle_server_messages, args=(self.client, self.game_window), daemon=True).start()
            self.game_window.show()
            self.close()  # Close welcome screen


class GameWindow(QMainWindow, Ui_GameWindow):
    def __init__(self, client):
        super().__init__()
        self.overlay = QLabel(self)
        self.client = client
        self.displayed_players = set()
        self.saved_text = ""
        self.player_hearts = {}  # maps player name -> QLabel showing their hearts
        self.setupUi(self)
        self.hearts_dic = {}

        # Connect UI events
        self.input_box.textChanged.connect(self.save_input)
        self.input_box.returnPressed.connect(self.send_input)
        self.input_box.setEnabled(False)
        self.start_button.clicked.connect(self.start_game)
        self.start_button.setEnabled(False)

    def fill_players_hearts(self, players_names, lives):
        for name in players_names:
            print(name)
            self.hearts_dic[name] = lives
        print(self.hearts_dic)

    def update_player_list(self, player_names):
        self._player_names_to_update = player_names
        QTimer.singleShot(0, self._apply_player_list_update)

    def _apply_player_list_update(self):
        self.clear_player_list()
        self.player_hearts.clear()

        for name in self._player_names_to_update:
            container = QWidget()
            layout = QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(15)

            # Clean dark translucent background
            container.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0.4);  /* Soft dark glass */
                border-radius: 12px;
                margin: 5px;
            """)

            # Player name label
            name_label = QLabel(name)
            name_label.setStyleSheet("""
                color: white;
                font-weight: 600;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
            """)

            # Hearts label
            if self.hearts_dic:
                hearts_label = QLabel("❤️" * self.hearts_dic[name])
            else:
                hearts_label = QLabel("❤️❤️❤️")
            hearts_label.setStyleSheet("""
                font-size: 18px;
                margin-left: 5px;
            """)

            layout.addWidget(name_label)
            layout.addWidget(hearts_label)

            self.player_list_layout.addWidget(container)

            self.displayed_players.add(name)
            self.player_hearts[name] = hearts_label  # Store for future updates

    def update_hearts(self, name, hearts):
        self.hearts_dic[name] = hearts
        if name in self.displayed_players:
            self.player_hearts[name].setText("❤️" * hearts)

    def clear_player_list(self):
        while self.player_list_layout.count():
            item = self.player_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def show_game_over(self, result: str):
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if result == "WIN":
            text = "🏆 YOU WIN 🏆"
            color = "gold"
        else:
            text = "💥 YOU LOSE 💥"
            color = "red"

        self.overlay.setText(text)
        self.overlay.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 180);
            color: {color};
            font-size: 48px;
            font-weight: bold;
            border: 4px solid white;
            border-radius: 20px;
        """)
        self.overlay.raise_()  # Bring to front
        self.overlay.show()

    def update_info_text(self, text):
        self.letters_label.setText(text)
        self.letters_label.setStyleSheet("""
            color: white;
            background-color: rgba(0, 0, 0, 0.6);  /* semi-transparent black */
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 32px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.letters_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-size: 20px;
            font-weight: bold;
            background-color: rgba(0, 0, 0, 0.6);
            border-radius: 8px;
            padding: 6px 10px;
        """)

    def set_input_enabled(self, state: bool):
        self.input_box.setDisabled(not state)

    def display_inputs_of_other_clients(self, client_inputs):
        self.input_box.setText(client_inputs)

    def save_input(self, text):
        self.saved_text = text
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
    # ip = '192.168.68.55'
    port = 65432
    app = QApplication([])

    client = Client(ip, port)
    client.connect_to_server()
    window = Window(client)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()