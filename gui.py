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
import sys
import queue
import logging
import time
import meamer
import demo_receiver
from multiprocessing import Process
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, \
    QDesktopWidget, QLineEdit, QFormLayout, QMainWindow, QLabel, QTextEdit, \
    QAbstractScrollArea, QFileDialog
from PyQt5.QtGui import QIcon, QFont, QTextCharFormat, QBrush, QColor, QTextCursor, \
    QTextFormat, QCursor
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import QCoreApplication, QPoint, Qt, QThread, pyqtSignal, QObject, \
    pyqtSlot
from PyQt5 import uic


MAINWINDOW_UI_FILE = 'style/interface.ui'
DEMOWINDOW_UI_FILE = 'style/demo.ui'
MAINWINDOW_CSS_FILE = 'style/stylesheet.css'
grinderStarted = False
grinderStarted = False


# We _need_ a synchronized queue to handle outputting to the status
# area in a separate thread so we don't block.
class LogStream(object):
    def __init__(self, q):
        self.q = q


    def write(self, text):
        self.q.put(text)


    def flush(self):
        self.q.queue.clear()


class QLogOutputter(QObject):
    stdout_signal = pyqtSignal(str)
    running = True

    def __init__(self, q, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.q = q


    @pyqtSlot()
    def run(self):
        while self.running:
            text = self.q.get()
            self.stdout_signal.emit(text)


class QLoggingHandler(logging.Handler):
    logging_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(self.logging_format))


    def emit(self, record):
        print(self.format(record))


def fork_cleaviz():
    cleaviz_window = cleaviz.CleavizWindow(sample_rate=10000, segment_length=1000)
    cleaviz_window.run()


def analysis_loading(func):
    def wrapper(self, example):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        example()
        QApplication.restoreOverrideCursor()
    return wrapper


class DemoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()


    def init_ui(self):
        uic.loadUi(DEMOWINDOW_UI_FILE, self)

        self.checkSensorButton.clicked.connect(self.set_sensor_status)
        self.initDemoButton.clicked.connect(self.run_demo)

        # Events.
        self.closeEvent = self.close_event

        self.demo_running = False

        self.show()

        self.checkSensorButton.setAutoFillBackground(True)
        self.initDemoButton.setAutoFillBackground(True)


    def close_event(self, event):
        try:
            self.demo_running = False
            self.demo_thread.join()
        except AttributeError as e:
            pass


    def set_sensor_status(self):
        if demo_receiver.check_sensor_active():
            self.sensorStatus.setStyleSheet('background-color: "#21c226"')
        else:
            self.sensorStatus.setStyleSheet('background-color: "red"')


    # Needed as an inner thread to keep the GUI responsive during
    # demo. This is the cleanest way we found to make sure that we can
    # exit the demo window and make sure that the demo ends.
    def _run_demo(self):
        self.demo_running = True
        self._demo_thread = sthread.StoppableThread(
            target=demo_receiver.connect_to_grinder, args=(False,))
        self._demo_thread.start()

        while self.demo_running:
            if not demo_receiver.prediction_event.wait(timeout=1):
                continue
            else:
                color = 'red' if not demo_receiver.stimuli_state else 'green'
                self.distanceStatus.setStyleSheet('background-color: {};'.format(color))
                demo_receiver.prediction_event.clear()

        self._demo_thread.stop()
        self._demo_thread.join()


    def run_demo(self):
        self.demo_thread = sthread.StoppableThread(target=self._run_demo)
        self.demo_thread.start()



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
        # self.setWindowIcon(QIcon('style/SiNRI_logo.svg'))

        with open(MAINWINDOW_CSS_FILE) as style_file:
            self.setStyleSheet(style_file.read())

        self.startMockButton.clicked.connect(self.toggle_mock)
        self.startGrinderButton.clicked.connect(self.toggle_grinder)
        self.startCleavizButton.clicked.connect(self.start_cleaviz)
        self.startDemoButton.clicked.connect(self.init_demo_widget)

        self.stimuliSetupButton.clicked.connect(self.setup_stimuli)
        self.stimuliStartButton.clicked.connect(self.start_stimuli)
        self.stimuliStopButton.clicked.connect(self.stop_stimuli)

        self.selectExperimentButton.clicked.connect(self.select_experiment)
        self.bucketingButton.clicked.connect(
            lambda: print(threading.enumerate()) and self.run_analysis_example(analysis.bucketing_example))
        self.plottingButton.clicked.connect(
            lambda: self.run_analysis_example(analysis.plotting_example))
        self.peakDetectionButton.clicked.connect(
            lambda: self.run_analysis_example(analysis.peak_detection_example))
        self.summaryButton.clicked.connect(
            lambda: self.run_analysis_example(analysis.peak_detection_summary_example))
        self.smaButton.clicked.connect(
            lambda: self.run_analysis_example(analysis.simple_moving_average_example))
        self.spectralAnalysisButton.clicked.connect(
            lambda: self.run_analysis_example(analysis.spectral_analysis_example))

        # Events.
        self.closeEvent = self.close_event
        self.setWindowIcon(QIcon('style/img/bs19_yellow_icon.png'))

        self.show()

        # I have no idea why this is needed, the designer is not of
        # much help here. Jeez.
        self.startGrinderButton.setAutoFillBackground(True)
        self.startMockButton.setAutoFillBackground(True)
        self.startCleavizButton.setAutoFillBackground(True)
        self.stimuliSetupButton.setAutoFillBackground(True)
        self.stimuliStartButton.setAutoFillBackground(True)
        self.stimuliStopButton.setAutoFillBackground(True)

        # Connect stdout to the status area, as this needs to be
        # synchronized with a blocking queue.
        self.add_custom_log_handler()
        self.log_q = queue.Queue()
        self.log_stream = LogStream(self.log_q)
        sys.stdout = self.log_stream

        self.log_t = QThread()
        self.log_signal_obj = QLogOutputter(self.log_q)
        self.log_signal_obj.stdout_signal.connect(self.output_log)
        self.log_signal_obj.moveToThread(self.log_t)
        self.log_t.started.connect(self.log_signal_obj.run)
        self.log_t.start()

        self.mock_running = False
        self.grinder_running = False

        self.meamer = meamer.MEAMEr('10.20.92.130')


    def close_event(self, event):
        self.log_signal_obj.running = False

        if self.mock_running:
            self.stop_mock()
        if self.grinder_running:
            self.stop_grinder()

        # We need to force re-evaluation of logging thread with print
        # to exit.
        print('Logging thread exited')
        self.log_t.terminate()
        self.log_t.wait()


    def add_custom_log_handler(self):
        self.logging_handler = QLoggingHandler()
        for logger_str in logging.root.manager.loggerDict:
            logging.getLogger(logger_str).addHandler(self.logging_handler)


    def output_log(self, text):
        self.logArea.moveCursor(QTextCursor.End)
        self.logArea.insertPlainText(text)


    def start_cleaviz(self):
        p = Process(target=fork_cleaviz)
        p.start()


    def init_demo_widget(self):
        self.demo_widget = DemoWidget()


    def change_button_colors(self, btn, background, color):
        btn.setStyleSheet('background-color: {};'
                          'color: {};'.format(background, color))
        btn.setAutoFillBackground(True)


    def set_button_style(self, btn, background, color, text):
        self.change_button_colors(btn, background, color)
        btn.setText(text)


    def start_mock(self):
        try:
            if not self.mockThread.stopped():
                return
        except AttributeError:
            pass

        meame_mock = mock.MEAMEMock(12340)
        self.mockThread = sthread.StoppableThread(target=meame_mock.run)
        self.mockThread.start()


    def stop_mock(self):
        self.mockThread.stop()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('localhost', 12340))
            except ConnectionRefusedError:
                pass
        self.mockThread.join()


    def toggle_mock(self):
        self.mock_running = self.mock_running ^ True

        if self.mock_running:
            self.start_mock()
            self.set_button_style(self.startMockButton, 'red', 'white', 'STOP MOCK')
        else:
            self.stop_mock()
            self.set_button_style(self.startMockButton, '#21c226', 'white', 'START MOCK')


    def _start_grinder(self):
        try:
            self.server = grinder.Server(8080,
                                         reflect=False,
                                         meame_addr="10.20.92.130")
            self.server.listen()
        except Exception as e:
            logger.info('Shutting down gracefully')
            self.server.socket.shutdown(socket.SHUT_RDWR)


    def start_grinder(self):
        self.grndThread = sthread.StoppableThread(target=self._start_grinder, args=(), kwargs={})
        self.grndThread.start()


    def stop_grinder(self):
        self.grndThread.stop()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 8080))
        except ConnectionRefusedError as e:
            pass
        self.grndThread.join()


    def toggle_grinder(self):
        time.sleep(0.01)
        self.grinder_running = self.grinder_running ^ True

        if self.grinder_running:
            self.start_grinder()
            self.set_button_style(self.startGrinderButton, 'red', 'white', 'STOP GRINDER')
        else:
            self.stop_grinder()
            self.set_button_style(self.startGrinderButton, '#21c226', 'white', 'START GRINDER')


    def setup_stimuli(self):
        self.meamer.setup_stim()


    def start_stimuli(self):
        self.meamer.start_stim()
        self.meamer.setup_stim()


    def stop_stimuli(self):
        self.meamer.stop_stim()


    def select_experiment(self):
        logger.info("Browsing Experiment Files...")
        file_name, _ = QFileDialog.getOpenFileName(self, str("Open File"), './mea_data')
        if file_name:
            logger.info("Setting file name: " + file_name)
            analysis.experiment_fp = file_name


    # Not strictly needed anymore, was used for threading before.
    @analysis_loading
    def run_analysis_example(self, example):
        example()


def main():
    app = pg.QtGui.QApplication([])
    main_window = MainWindow()
    app.exec_()


if __name__ == '__main__':
    main()
