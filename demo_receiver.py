import log
logger = log.get_logger(__name__)


import socket
import traceback
import struct
import numpy as np
import serial
import sthread
import time
import meamer
import sthread
import warnings
import threading


sensor_distance = 1500
sensor_distances = []
is_object_close = False
prediction_event = threading.Event()
stimuli_state = False


def check_sensor_active():
    try:
        with serial.Serial('/dev/ttyUSB5') as ser:
            return True
    except serial.serialutil.SerialException as e:
        return False


def serial_distance(serial_connection):
    return int(serial_connection.readline().strip())


def receive_sensor():
    """
    Receives a single reading from the external ultrasound sensor.
    """
    global sensor_distance
    global sensor_distances
    global is_object_close

    with serial.Serial('/dev/ttyUSB5') as ser:
        while True:
            sensor_distance = serial_distance(ser)
            sensor_distances.append(1.0 if sensor_distance < 100.0 else 0.0)
            sensor_distances = sensor_distances[-10:]

            if np.mean(sensor_distances) >= 0.6:
                is_object_close = True
            else:
                is_object_close = False

            if sthread.check_terminate_thread():
                return


def connect_to_grinder(verbose=True):
    host = '0.0.0.0'
    port = 8080

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            run_demo(s, verbose)
    except Exception as e:
        logger.info('Could not connect to remote grinder instance')
        logger.error(traceback.format_exc())


def receive_segment(segment_length, s):
    """
    <segment_length> determines the size of each segment of the
    interleaved stream. <s> is socket that listens for the incoming
    stream.
    """
    bytes_received = 0
    segment_data = bytearray(b'')
    channel_data = []

    while True:
        data = s.recv(segment_length*4 - bytes_received)
        bytes_received = bytes_received + len(data)
        segment_data.extend(data)

        if (bytes_received != segment_length*4):
            continue

        for i in struct.iter_unpack('f', segment_data):
                channel_data.append(i[0])

        return channel_data


def run_demo(connection, verbose=True):
    global stimuli_state

    meame = meamer.MEAMEr('10.20.92.130')
    SMA_amplitude_threshold = 1e-5
    peak_amplitude_threshold = 7.3e-5
    current_segment = 0
    window_size = 10
    previous_predictions = []
    previous_object_state = False
    sensor_thread = sthread.StoppableThread(target=receive_sensor)
    sensor_thread.start()

    try:
        while True:
            if sthread.check_terminate_thread():
                sensor_thread.stop()
                sensor_thread.join()
                return

            segment = receive_segment(segment_length=1000, connection=connection)

            if current_segment == 0:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', category=RuntimeWarning)
                    if verbose:
                        logger.info('A second has passed, {}, {}, {}'.
                                    format(abs(np.mean(segment)),
                                           np.max(segment),
                                           np.mean(previous_predictions)))

            current_segment = (current_segment + 1) % window_size

            if abs(np.mean(segment))>= SMA_amplitude_threshold or \
               np.max(segment) >= peak_amplitude_threshold:
                prediction = 1.0
            else:
                prediction = 0.0

            # We keep a window of size <window_size> of the previous
            # predictions both for whether the external sensor is
            # outputting an object closeby, but also for whether we
            # are seeing stimuli in the received data stream. If quite
            # a few of the predictions in this current window are
            # positive, we determine that we should act.
            previous_predictions.append(prediction)
            previous_predictions = previous_predictions[-window_size:]

            if (np.mean(previous_predictions) >= 0.5):
                if not stimuli_state:
                    prediction_event.set()
                stimuli_state = True
            else:
                if stimuli_state:
                    prediction_event.set()
                stimuli_state = False

            if previous_object_state != is_object_close:
                previous_object_state ^= True

                if previous_object_state:
                    meame.start_stim()
                    meame.setup_stim()
                    if verbose:
                        logger.info('Started remote MEAME stimuli')
                else:
                    meame.stop_stim()
                    if verbose:
                        logger.info('Stopped remote MEAME stimuli')

    except KeyboardInterrupt as e:
        sensor_thread.stop()


def main():
    connect_to_grinder()


if __name__ == '__main__':
    main()
