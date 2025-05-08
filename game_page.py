from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton
import sys


class SimpleInputBox(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client  # Reference to the client for server communication
        self.saved_text = ""  # Stores current input
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Info label - displays game status (e.g., "Waiting for other players...")
        self.info_label = QLabel("Waiting for other players...")
        layout.addWidget(self.info_label)

        # Status label - used for dynamic messages (e.g., errors, instructions)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Input field for typing answers
        self.input_box = QLineEdit(self)
        self.input_box.textChanged.connect(self.save_input)  # Called on each keystroke
        self.input_box.returnPressed.connect(self.send_input)  # Called on Enter key

        # Start game button (disabled and hidden by default)
        self.start_button = QPushButton("Start Game", self)
        self.start_button.clicked.connect(self.start_game)

        # Add widgets to layout
        layout.addWidget(self.input_box)
        layout.addWidget(self.start_button)

        # Apply layout and styling
        self.setLayout(layout)
        self.setWindowTitle("BombParty Game Window")
        self.apply_styles()

        # Initial widget states
        self.set_input_enabled(False)
        self.start_button.setEnabled(False)
        self.start_button.hide()

        self.showMaximized()  # ⬅️ Make the window full screen

    # ----------------------
    # UI Behavior Functions
    # ----------------------

    def apply_styles(self):
        """Set the visual style of the window and widgets."""
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
        """Update the top info label (e.g., change instructions)."""
        self.info_label.setText(text)

    def update_status(self, message, color):
        """Display a status message with a custom color."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold;"
        )

    def set_input_enabled(self, state: bool):
        """Enable or disable the input field."""
        self.input_box.setDisabled(not state)

    def display_inputs_of_other_clients(self, client_inputs):
        """Set the input box to show input from other players (could override your own text)."""
        self.input_box.setText(client_inputs)

    # ----------------------
    # Input Logic
    # ----------------------

    def save_input(self, text):
        """Triggered on each character typed - saves and sends to server."""
        self.saved_text = text
        self.client.send_message(f"INPUT_CLIENT|{text}\n")

    def send_input(self):
        """Send 'ENTER' command when user presses Enter key."""
        self.client.send_message("INPUT_CLIENT|ENTER\n")
        self.clear_input()

    def clear_input(self):
        """Clear the input box and saved input."""
        self.input_box.clear()
        self.saved_text = ""

    # ----------------------
    # Game Control
    # ----------------------

    def start_game(self):
        """Send start game signal to the server."""
        self.client.send_message("BUTTON|START_GAME\n")
