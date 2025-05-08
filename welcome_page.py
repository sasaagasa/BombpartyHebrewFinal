from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class WelcomeScreen(QWidget):
    def __init__(self, switch_to_game_callback):
        super().__init__()
        self.switch_to_game = switch_to_game_callback
        self.initUI()

    def initUI(self):
        self.setWindowTitle("BombParty")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add logo image
        logo = QLabel()
        pixmap = QPixmap("logo.png")  # Make sure logo.png is in your working directory
        pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        # Nickname label
        nickname_label = QLabel("Enter your nickname:")
        nickname_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nickname_label.setStyleSheet("font-size: 20px; color: white; margin-bottom: 10px;")
        layout.addWidget(nickname_label)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your name")
        self.name_input.setFixedHeight(50)
        self.name_input.setStyleSheet("font-size: 20px; padding: 10px;")
        layout.addWidget(self.name_input)

        # Start button
        start_button = QPushButton("OK")
        start_button.setFixedHeight(40)
        start_button.setStyleSheet(
            "font-size: 18px; background-color: #2e86de; color: white; border-radius: 10px;"
        )
        start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(start_button)

        self.setLayout(layout)
        self.showMaximized()  # ⬅️ Make the window full screen


    def on_start_clicked(self):
        name = self.name_input.text().strip()
        if name:
            self.switch_to_game(name)
