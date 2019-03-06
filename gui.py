import cleaviz
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, \
    QDesktopWidget, QLineEdit, QFormLayout, QMainWindow, QLabel, QTextEdit, \
    QAbstractScrollArea
from PyQt5.QtGui import QIcon, QFont, QTextCharFormat, QBrush, QColor, QTextCursor, \
    QTextFormat, QCursor
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import QCoreApplication, QPoint, Qt, QThread, pyqtSignal
from PyQt5 import uic


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()


    def init_ui(self):
        uic.loadUi('style/interface.ui', self)
        self.show()



def main():
    app = pg.QtGui.QApplication([])
    # win = cleaviz.CleavizWindow(sample_rate=10000, segment_length=100)
    main_window = MainWindow()
    app.exec_()

if __name__ == '__main__':
    main()