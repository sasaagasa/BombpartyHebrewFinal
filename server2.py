import requests
from bs4 import BeautifulSoup
import random
import socket
import threading


def generate_random_hebrew_letters():
    hebrew_letters = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט',
                      'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ',
                      'ק', 'ר', 'ש', 'ת']
    return ''.join(random.sample(hebrew_letters, 2))


# Map Hebrew final letters to normal forms
final_letters = {
    'ך': 'כ',
    'ם': 'מ',
    'ן': 'נ',
    'ף': 'פ',
    'ץ': 'צ'
}


# Function to normalize a word (replace final forms with normal ones)
def normalize(word):
    return ''.join(final_letters.get(c, c) for c in word)


# Function to load words and generate sequences
def generate_sequences(file_path):
    with open(file_path, encoding='utf-8') as f:
        words = [normalize(line.strip()) for line in f if line.strip()]

    sequences_2 = set()
    sequences_3 = set()

    for word in words:
        length = len(word)
        for i in range(length - 1):  # 2-letter sequences
            sequences_2.add(word[i:i + 2])
        for i in range(length - 2):  # 3-letter sequences
            sequences_3.add(word[i:i + 3])
    print(sequences_2, '\n')
    print(sequences_3)
    return list(sequences_2), list(sequences_3)


# Function to pick a random sequence
def pick_sequence(sequences_2, sequences_3):
    if random.random() < 0.7:
        # 70% chance for 2-letter
        return random.choice(sequences_2)
    else:
        # 30% chance for 3-letter
        return random.choice(sequences_3)


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
            # print(f"player{self.id},sent:  {message}")
            if message:
                self.socket.sendall(message.encode())  # Send encoded message
                print(f"send to client:{message}")
        except (ConnectionResetError, BrokenPipeError, OSError):
            self.server.remove_completely(self)  # close connection with client
        except Exception as e:
            print(f"Error sending to {self.name}: {e}")

    def set_letters(self, letters):
        self.letters = letters

    def receive_message(self):
        """Receive a message from the player (blocking)."""
        try:
            data = self.socket.recv(1024).decode()
            messages = data.split("\n")
            for msg in messages:
                print(f"rcv: {msg} from player{self.id}")
                return msg  # Receive and decode message
        except socket.timeout:
            raise  # Let timeout propagate so `get_word` can catch it
        except (ConnectionResetError, BrokenPipeError, OSError):
            self.server.remove_completely(self)  # close connection with client
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
        self.socket.connected()

    def settimeout(self, timeout):
        self.socket.settimeout(timeout)  # Pass timeout to the actual socket


class Server:
    def __init__(self, ip="0.0.0.0", port=65432):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TIME_LIMIT = 5
        self.start_game = False
        self.playing_players = []
        self.all_players = []
        self.used_words = set()
        self.num_player = 0

    def add_player(self, client_socket, name):
        self.num_player += 1
        player = Player(name, client_socket, self.num_player, self)
        self.playing_players.append(player)
        self.all_players.append(player)
        self.broadcast_player_list()  # 🔁 Notify all clients

        admin = self.playing_players[0]
        if len(self.playing_players) >= 2 and not self.start_game:
            admin.send_message("ADMIN|YOU_ARE_THE_HOST:")
            self.before_game_start(admin)

    def before_game_start(self, admin):
        names = [p.name for p in self.playing_players]
        while not self.start_game and len(self.playing_players) >= 2:
            message = admin.receive_message()
            print(f"in while {message}")
            if message == "BUTTON|START_GAME":
                self.start_game = True
                for player in self.playing_players:
                    player.send_message(f"ADMIN|GAME_STARTED:"+",".join(names))
                random.shuffle(self.playing_players)
                threading.Thread(target=self.manage_turns, daemon=True).start()

    def remove_completely(self, player):
        if player in self.all_players:
            self.all_players.remove(player)
            print(f"{player.name} disconnected")
            player.socket.close()

    def move_to_spectate(self, player):
        if player in self.playing_players:
            self.playing_players.remove(player)
            self.broadcast_player_list()  # 🔁 Notify all clients

    def update_input(self, current_client, text):
        for player in self.all_players:
            if current_client.id != player.id and text not in (None, "ENTER"):
                player.send_message(f"UPDATE_INPUT|{text}\n")

    def update_all_client(self, current_player):
        for player in self.all_players:
            if player.id != current_player.id:
                message = f"UPDATE_LETTERS|{current_player.letters}\n"
                print(f"Sending to {player.name}: {message}")  # Log the message
                player.send_message(message)

    def broadcast_player_list(self):
        names = [p.name for p in self.playing_players]
        message = "PLAYER_LIST|" + ",".join(names) + "\n"
        for player in self.all_players:
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
        sequences_2, sequences_3 = generate_sequences('word_list.txt')
        while len(self.playing_players) > 1:
            current_player = self.playing_players[0]  # Get the first player in the list
            challenge = pick_sequence(sequences_2, sequences_3)
            # Notify player that it's their turn
            current_player.send_message(f"TURN_START|{challenge}\n")
            print(f"server: It's {current_player.name}'s turn. Letters: {challenge}")
            current_player.set_letters(challenge)  # set the letters in player
            self.update_all_client(current_player)
            timer_expired = threading.Event()

            # start timer
            timer = threading.Timer(5, self.timeout, args=(timer_expired,))
            timer.start()

            while not timer_expired.is_set() and current_player in self.playing_players:
                word = self.get_word(current_player, timer_expired)
                print(f"***{word}***")
                if word is not None and verify(word, challenge) and word not in self.used_words:
                    timer.cancel()  # cancel timer
                    self.used_words.add(word)
                    current_player.send_message("VALID_WORD|Turn over\n")
                    break
                elif word in self.used_words:
                    current_player.send_message(f"USED_WORD|Try again. Letters: {challenge}\n")
                else:
                    current_player.send_message(f"INVALID_WORD|Try again. Letters: {challenge}\n")

            else:
                current_player.send_message("TIME_UP|You lost a life!\n")
                current_player.lose_life()
                for player in self.all_players:
                    player.send_message(f"PLAYER_LOST_LIFE|{current_player.name}:{current_player.get_life()}\n")

            if current_player.get_life() == 0:
                self.move_to_spectate(current_player)  # remove the player from the playing list

                if len(self.playing_players) == 1:
                    self.playing_players[0].send_message("GAME_OVER|WIN\n")
                    for player in self.all_players:
                        if player.id != self.playing_players[0].id:
                            player.send_message("GAME_OVER|LOSE\n")

            else:
                self.playing_players.append(self.playing_players.pop(0))  # Move to the next player

    def handle_client(self, client_socket, client_address):
        print(f"[SERVER] New connection from {client_address}")
        name = client_socket.recv(1024).decode()
        print(name)
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
