import log
logger = log.get_logger(__name__)
import threading
import cleaviz
import mock
import grinder
import pyqtgraph as pg
import socket
import sthread
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, \
    QDesktopWidget, QLineEdit, QFormLayout, QMainWindow, QLabel, QTextEdit, \
    QAbstractScrollArea
from PyQt5.QtGui import QIcon, QFont, QTextCharFormat, QBrush, QColor, QTextCursor, \
    QTextFormat, QCursor
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import QCoreApplication, QPoint, Qt, QThread, pyqtSignal
from PyQt5 import uic

MAINWINDOW_UI_FILE = 'style/interface.ui'
MAINWINDOW_CSS_FILE = 'style/stylesheet.css'

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        uic.loadUi(MAINWINDOW_UI_FILE, self)
        self.setWindowTitle('SiNRI')
        self.setObjectName("SiNRI")

        with open(MAINWINDOW_CSS_FILE) as style_file:
            self.setStyleSheet(style_file.read())

        self.startMockButton.clicked.connect(self.startMock)
        self.StartGrinderButton.clicked.connect(self.startGrinder)
        self.startCleavizButton.clicked.connect(self.startCleaviz)
        self.stopMockButton.clicked.connect(self.stopMock)

        self.show()


    def startCleaviz(self):
        cleaviz.CleavizWindow(sample_rate=10000, segment_length=100)


    def startMock(self):
        # TODO: Fix runningBar change color on run/stop
        self.runningStatusBar.setStyleSheet("#runningStatusBar{background-color: rgb(72, 224, 31}")
        meameMock = mock.MEAMEMock(12340)
        self.mockThread = sthread.StoppableThread(target=meameMock.run)
        self.mockThread.start()


    def stopMock(self):
        self.mockThread.stop()
        self.mockThread.join()


    def startGrinder(self):
        def startGinderThread():
            try:
                server = grinder.Server(8080,
                                reflect=True,
                                meame_addr="localhost")
                server.listen()
            except Exception as e:
                logger.info('Shutting down gracefully')
                server.socket.shutdown(socket.SHUT_RDWR)

        grndThread = threading.Thread(target=startGinderThread, args=(), kwargs={})
        grndThread.start()


def main():
    app = pg.QtGui.QApplication([])
    main_window = MainWindow()
    app.exec_()

if __name__ == '__main__':
    main()