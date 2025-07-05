from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QStatusBar, QMenuBar, QWidget, QVBoxLayout
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Template Application")

        # Menubar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Status bar
        statusbar = QStatusBar(self)
        self.setStatusBar(statusbar)
        statusbar.showMessage("Ready")

        # Central widget with Hello World label
        central_widget = QWidget(self)
        layout = QVBoxLayout()
        label = QLabel("Hello, World!", self)
        layout.addWidget(label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
