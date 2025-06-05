from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_GameWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("GameWindow")
        MainWindow.setWindowTitle("BombParty Game")
        MainWindow.setStyleSheet("""
            QMainWindow {
                border-image: url(images/GameBackground.jpg);
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: rgba(44, 44, 44, 0.9);
                color: white;
                padding: 10px;
                border: 2px solid #555;
                border-radius: 10px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #FFA500;
            }
            QPushButton {
                background-color: #FFA500;
                color: black;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ffbb33;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(40, 40, 40, 40)
        self.verticalLayout.setSpacing(20)

        self.title = QtWidgets.QLabel("BombParty Lobby", self.centralwidget)
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setStyleSheet("color: #FFA500;")
        self.verticalLayout.addWidget(self.title)

        # Scroll Area for players
        self.scroll_area = QtWidgets.QScrollArea(self.centralwidget)
        self.scroll_area.setFixedHeight(250)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        self.player_list_widget = QtWidgets.QWidget()
        self.player_list_layout = QtWidgets.QVBoxLayout(self.player_list_widget)
        self.scroll_area.setWidget(self.player_list_widget)
        self.verticalLayout.addWidget(self.scroll_area)

        # Info label
        self.letters_label = QtWidgets.QLabel("Waiting for other players...", self.centralwidget)
        self.letters_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.letters_label.setStyleSheet("font-size: 18px; color: #ddd;")
        self.verticalLayout.addWidget(self.letters_label)

        # Status label
        self.status_label = QtWidgets.QLabel("", self.centralwidget)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.status_label)

        # Input box
        self.input_box = QtWidgets.QLineEdit(self.centralwidget)
        self.input_box.setPlaceholderText("Enter your word...")
        self.input_box.setFixedHeight(45)
        self.verticalLayout.addWidget(self.input_box)

        # Start button
        self.start_button = QtWidgets.QPushButton("Start Game", self.centralwidget)
        self.start_button.setFixedHeight(45)
        self.verticalLayout.addWidget(self.start_button)

        MainWindow.setCentralWidget(self.centralwidget)
