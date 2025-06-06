from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_GameWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("GameWindow")
        MainWindow.setWindowTitle("BombParty Game")
        MainWindow.setMinimumSize(600, 700)  # Optional: enforce minimum size

        # ✨ Main style sheet with background image
        MainWindow.setStyleSheet("""
            QMainWindow {
                background-image: url(images/Designer.jpg);
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', sans-serif;
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
                background-color: #ff9933;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ffaa44;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(40, 40, 40, 40)
        self.verticalLayout.setSpacing(25)

        # ✨ Title Label
        self.title = QtWidgets.QLabel("💣 BombParty 💣", self.centralwidget)
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = QtGui.QFont()
        font.setPointSize(36)
        font.setBold(True)
        font.setFamily("Segoe UI Black")
        self.title.setFont(font)
        self.title.setStyleSheet("color: orange; text-shadow: 2px 2px 4px black;")
        self.verticalLayout.addWidget(self.title)

        # ✨ Scroll Area for Players
        self.scroll_area = QtWidgets.QScrollArea(self.centralwidget)
        self.scroll_area.setFixedHeight(250)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent")

        self.player_list_widget = QtWidgets.QWidget()
        self.player_list_layout = QtWidgets.QVBoxLayout(self.player_list_widget)
        self.scroll_area.setWidget(self.player_list_widget)
        self.verticalLayout.addWidget(self.scroll_area)

        # ✨ Info Label
        self.letters_label = QtWidgets.QLabel("Waiting for other players...", self.centralwidget)
        self.letters_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.letters_label.setStyleSheet("""
            font-size: 20px;
            color: #000000;
            font-weight: 500;
            text-shadow: 1px 1px 3px #000;
        """)
        self.verticalLayout.addWidget(self.letters_label)

        # Status Label (empty by default)
        self.status_label = QtWidgets.QLabel("", self.centralwidget)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #FF6666; font-size: 16px;")
        self.verticalLayout.addWidget(self.status_label)

        # ✨ Input Box
        self.input_box = QtWidgets.QLineEdit(self.centralwidget)
        self.input_box.setFixedHeight(50)
        self.verticalLayout.addWidget(self.input_box)

        # ✨ Start Button
        self.start_button = QtWidgets.QPushButton("▶ Start Game", self.centralwidget)
        self.start_button.setFixedHeight(50)
        self.verticalLayout.addWidget(self.start_button)

        MainWindow.setCentralWidget(self.centralwidget)
