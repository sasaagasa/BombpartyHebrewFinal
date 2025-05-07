import socket
import threading

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton
import sys


class SimpleInputBox(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("Waiting for other players...")
        layout.addWidget(self.info_label)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.input_box = QLineEdit(self)
        self.input_box.textChanged.connect(self.save_input)
        self.input_box.returnPressed.connect(self.send_input)
        self.start_button = QPushButton("Start Game", self)
        self.start_button.clicked.connect(self.start_game)  # Connect button to function
        self.apply_styles()

        layout.addWidget(self.input_box)
        layout.addWidget(self.start_button)
        self.setLayout(layout)
        self.setWindowTitle("BombParty Game Window")

        self.saved_text = ""
        self.set_input_enabled(False)
        self.start_button.setEnabled(False)  # Disable after starting
        self.start_button.hide()  # Hide the button





    def update_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")

    def start_game(self):
        """Sends a start command to the server and disables the button."""
        self.client.send_message("BUTTON|START_GAME\n")  # Send start command

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298
                );
                color: #ffffff;
                font-family: 'Arial';
                font-size: 16px;
            }

            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffcc00;
            }

            QLineEdit {
                background-color: #1e1e1e;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 10px;
                color: #ffffff;
                font-size: 18px;
            }

            QLineEdit:disabled {
                background-color: #555;
                border: 2px solid #888;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 18px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def set_window_title(self, title):
        """Set the window title dynamically."""
        self.setWindowTitle(title)

    def update_info_text(self, text):
        self.info_label.setText(text)

    def save_input(self, text):
        self.saved_text = text
        self.client.send_message(f"INPUT_CLIENT|{text}\n")  # Send the current input to the server

    def send_input(self):
        """Send 'ENTER' when the player presses Enter and clear the input box."""
        self.client.send_message("INPUT_CLIENT|ENTER\n")
        self.clear_input()

    def clear_input(self):
        self.input_box.clear()
        self.saved_text = ""

    def set_input_enabled(self, state: bool):
        """Enable or disable the input box."""
        self.input_box.setDisabled(not state)

    def display_inputs_of_other_clients(self, client_inputs):
        """Display the inputs of other clients in the input box."""
        self.input_box.setText(client_inputs)


class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = None

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))
        name = "client2"
        self.send_message(name)
        print("Connected as client 2")

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
    app.quit()


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
    print("Time's up! You lose 1 life.")
    window.set_input_enabled(False)
    window.clear_input()
    window.update_status("⏰ Time's Up!", "orange")


def handle_invalid_word(window, retry_message):
    print(retry_message)
    window.update_status("❌ Invalid Word, try again!", "red")


def handle_admin(window, value):
    if value == "GAME_STARTED":
        window.start_button.setEnabled(False)  # enable the button
        window.start_button.hide()  # show the button
    elif value == "YOU_ARE_THE_HOST":
        window.start_button.setEnabled(True)  # enable the button
        window.start_button.show()  # show the button


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
            "INVALID_WORD": lambda values: handle_invalid_word(window, values)
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


def main():
    ip = '127.0.0.1'
    port = 65432

    global app
    app = QApplication(sys.argv)

    client = Client(ip, port)
    client.connect_to_server()

    window = SimpleInputBox(client)
    window.show()

    # Start a thread to handle incoming messages
    message_thread = threading.Thread(target=handle_server_messages, args=(client, window))
    message_thread.daemon = True
    message_thread.start()

    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
