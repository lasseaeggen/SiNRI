import log
logger = log.get_logger(__name__)
import threading
import cleaviz
import mock
import grinder
import pyqtgraph as pg
import socket
import sthread
import multiprocessing
import analysis
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
        # This is required as Linux uses fork instead of spawn to
        # create the new window. This will crash with an X error if
        # the spawn method is not set.
        multiprocessing.set_start_method('spawn')

        uic.loadUi(MAINWINDOW_UI_FILE, self)
        self.setWindowTitle('SiNRI')
        self.setObjectName("SiNRI")

        with open(MAINWINDOW_CSS_FILE) as style_file:
            self.setStyleSheet(style_file.read())

        self.startMockButton.clicked.connect(self.startMock)
        self.startGrinderButton.clicked.connect(self.startGrinder)
        self.stopGrinderButton.clicked.connect(self.stopGrinder)
        self.startCleavizButton.clicked.connect(self.startCleaviz)
        self.stopMockButton.clicked.connect(self.stopMock)
        self.bucketingButton.clicked.connect()


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
        meame_mock = mock.MEAMEMock(12340)
        self.mockThread = sthread.StoppableThread(target=meame_mock.run)
        self.mockThread.start()


    def stopMock(self):
        self.runningStatusBar.setStyleSheet("#runningStatusBar { background-color: rgb(224, 3, 0); }")
        self.mockThread.stop()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 12340))
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
        self.grndThread = sthread.StoppableThread(target=self._startGrinder, args=(), kwargs={})
        self.grndThread.start()


    def stopGrinder(self):
        self.grndThread.stop()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 8080))
        self.grndThread.join()
        print("HELLO THERE")


def main():
    app = pg.QtGui.QApplication([])
    main_window = MainWindow()
    app.exec_()

if __name__ == '__main__':
    main()
