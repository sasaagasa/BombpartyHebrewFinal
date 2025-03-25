import requests
from bs4 import BeautifulSoup
import random
import socket
import threading
import time
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QLabel


def generate_random_hebrew_letters():
    hebrew_letters = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט',
                      'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ',
                      'ק', 'ר', 'ש', 'ת']
    return ''.join(random.sample(hebrew_letters, 2))


def verify(word, letters):
    if letters not in word:
        return False
    url = "https://milog.co.il/"
    response = requests.get(url + word)
    soup = BeautifulSoup(response.text, 'html.parser')
    div_content = soup.find('div', class_='sr_below_text')
    if div_content:
        sub_content = div_content.get_text().split(' ')
        return sub_content[0] == "התקבלו" and sub_content[1].isnumeric()
    return False


class Player:
    def __init__(self, name, socket, player_id, server, lives=3):
        self.name = name
        self.socket = socket  # Store the player's socket connection
        self.id = player_id
        self.lives = lives
        self.letters = ""
        self.server = server
        self.is_turn = False  # Track if it's their turn

    def send_message(self, message):
        """Send a message to the player via their socket."""
        try:
            print(f"player{self.id},sent:  {message}")
            self.socket.sendall(message.encode())  # Send encoded message
        except (ConnectionResetError, BrokenPipeError, OSError):
            self.server.remove_client(self)  # close connection with client
        except Exception as e:
            print(f"Error sending to {self.name}: {e}")

    def set_letters(self, letters):
        self.letters = letters

    def receive_message(self):
        """Receive a message from the player (blocking)."""
        try:
            return self.socket.recv(1024).decode()  # Receive and decode message
        except socket.timeout:
            raise  # Let timeout propagate so `get_word` can catch it
        except (ConnectionResetError, BrokenPipeError, OSError):
            self.server.remove_client(self)  # close connection with client
        except Exception as e:
            print(f"Error receiving from {self.name}: {e}")
            return None  # Return None for other errors

    def lose_life(self):
        """Reduce the player's lives when they fail a turn."""
        if self.lives > 0:
            self.lives -= 1
        return self.lives  # Return remaining lives

    def get_life(self):
        return self.lives  # Return remaining lives

    def is_connected(self):
        self.socket.connected

    def settimeout(self, timeout):
        self.socket.settimeout(timeout)  # Pass timeout to the actual socket


class Server:
    def __init__(self, ip="0.0.0.0", port=65432):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TIME_LIMIT = 5
        self.start_game = False
        self.players = []
        self.players_dic = {}
        self.num_player = 0

    def add_player(self, client_socket, name):
        self.num_player += 1
        player = Player(name, client_socket, self.num_player, self)
        self.players.append(player)
        self.players_dic[self.num_player] = player
        admin = self.players[0]
        if len(self.players) >= 2 and not self.start_game:
            admin.send_message("ADMIN|YOU_ARE_THE_HOST")
            self.before_game_start(admin)

    def before_game_start(self, admin):
        while not self.start_game and len(self.players) >= 2:
            message = admin.receive_message()
            print(f"in while {message}")
            if message == "BUTTON|START_GAME":
                self.start_game = True
                admin.send_message("ADMIN|GAME_STARTED")
                random.shuffle(self.players)
                threading.Thread(target=self.manage_turns, daemon=True).start()

    def remove_client(self, player):
        if player in self.players:
            self.players.remove(player)
            print(f"{player.name} disconnected")
            player.socket.close()

    def update_input(self, current_client, text):
        for player in self.players:
            if current_client.id != player.id and text not in (None, "ENTER"):
                player.send_message(f"UPDATE_INPUT|{text}\n")

    def update_all_client(self, current_player):
        for player in self.players:
            if player.id != current_player.id:
                message = f"UPDATE_LETTERS|{current_player.letters}\n"
                print(f"Sending to {player.name}: {message}")  # Log the message
                player.send_message(message)

    def get_word(self, player, timer_expired):
        text = ""
        try:
            player.settimeout(0.1)  # Reduce timeout to check for expired timer more frequently

            while not timer_expired.is_set():  # Keep checking if time expired
                try:
                    data = player.receive_message()
                    if data.count('|') == 1:  # Ensure exactly one separator
                        _, input_c = data.split('|', 1)  # Split only once
                        self.update_input(player, input_c)
                        if input_c == "ENTER":
                            return text
                        if input_c:
                            text = input_c
                except socket.timeout:
                    continue  # Instead of failing, keep looping to check if time expired
        except Exception as e:
            print(f"Error receiving message: {e}")

        return None  # If the timer expired, return None immediately

    @staticmethod
    def timeout(check_expired_thread):
        check_expired_thread.set()

    def manage_turns(self):
        while len(self.players) > 1:
            current_player = self.players[0]  # Get the first player in the list
            letters_str = generate_random_hebrew_letters()

            # Notify player that it's their turn
            current_player.send_message(f"TURN_START|{letters_str}\n")
            print(f"server: It's {current_player.name}'s turn. Letters: {letters_str}")
            current_player.set_letters(letters_str)  # set the letters in player
            self.update_all_client(current_player)

            timer_expired = threading.Event()

            # start timer
            timer = threading.Timer(10, self.timeout, args=(timer_expired,))
            timer.start()

            while not timer_expired.is_set() and current_player in self.players:
                word = self.get_word(current_player, timer_expired)
                # word = current_player.receive_message()
                if word is not None and verify(word, letters_str):
                    timer.cancel()  # cancel timer
                    current_player.send_message("VALID_WORD|Turn over\n")
                    break
                else:
                    current_player.send_message(f"INVALID_WORD|Try again. Letters: {letters_str}\n")

            else:
                current_player.send_message("TIME_UP|You lost a life!\n")
                current_player.lose_life()

            if current_player.get_life() == 0:
                current_player.send_message("GAME_OVER|You lose :(\n")
                self.remove_client(current_player)  # todo: do not remove player.

                if len(self.players) == 1:
                    self.players[0].send_message("GAME_OVER|You win!\n")
            else:
                self.players.append(self.players.pop(0))  # Move to the next player

    def handle_client(self, client_socket, client_address):
        print(f"[SERVER] New connection from {client_address}")
        name = client_socket.recv(1024).decode()
        self.add_player(client_socket, name)

    def start(self):
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen()
        print(f"[SERVER] Server is listening on {self.ip}:{self.port}")
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
            except KeyboardInterrupt:
                print("[SERVER] Shutting down...")
                break
        self.server_socket.close()


if __name__ == '__main__':
    Server().start()
