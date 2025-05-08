import socket
import threading
import sys
from PyQt6.QtWidgets import QApplication
from game_page import SimpleInputBox
from welcome_page import WelcomeScreen

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

class AppController:
    def __init__(self, app, client):
        self.app = app
        self.client = client
        self.welcome_screen = WelcomeScreen(self.switch_to_game)
        self.game_window = None

    def start(self):
        self.welcome_screen.show()

    def switch_to_game(self, name):
        self.client.send_message(name)  # Send the name to the server
        self.game_window = SimpleInputBox(self.client)
        self.game_window.show()
        self.welcome_screen.close()

        # Start server communication thread
        message_thread = threading.Thread(
            target=handle_server_messages, args=(self.client, self.game_window)
        )
        message_thread.daemon = True
        message_thread.start()


# --- main function ---
def main():
    app = QApplication(sys.argv)

    ip = '127.0.0.1'
    port = 65432

    client = Client(ip, port)
    client.connect_to_server()

    controller = AppController(app, client)
    controller.start()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()