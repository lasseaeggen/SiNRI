import log
logger = log.get_logger(__name__)
import threading
import cleaviz
import mock
import grinder
import pyqtgraph as pg
import socket
import sthread
from multiprocessing import Process
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


def forkCleaviz():
    cleaviz_window = cleaviz.CleavizWindow(sample_rate=10000, segment_length=100)
    cleaviz_window.run()

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
        self.startGrinderButton.clicked.connect(self.startGrinder)
        self.startCleavizButton.clicked.connect(self.startCleaviz)
        self.stopMockButton.clicked.connect(self.stopMock)


        self.show()


    def startCleaviz(self):
        p = Process(target=forkCleaviz)
        p.start()


    def startMock(self):
        try:
            if not self.mockThread.stopped():
                return
        except AttributeError:
            pass

        self.runningStatusBar.setStyleSheet("#runningStatusBar{background-color: rgb(72, 224, 31) }")
        meameMock = mock.MEAMEMock(12340)
        self.mockThread = sthread.StoppableThread(target=meameMock.run)
        self.mockThread.start()


    def stopMock(self):
        self.runningStatusBar.setStyleSheet("#runningStatusBar { background-color: rgb(224, 3, 0); }")
        self.mockThread.stop()
        self.mockThread.join()

    def _startGrinder(self):
        try:
            self.server = grinder.Server(8080,
                            reflect=True,
                            meame_addr="localhost")
            self.server.listen()
        except Exception as e:
            logger.info('Shutting down gracefully')
            self.server.socket.shutdown(socket.SHUT_RDWR)


    def startGrinder(self):
        grndThread = sthread.StoppableThread(target=self._startGrinder, args=(), kwargs={})
        grndThread.start()


def main():
    app = pg.QtGui.QApplication([])
    main_window = MainWindow()
    app.exec_()

if __name__ == '__main__':
    main()