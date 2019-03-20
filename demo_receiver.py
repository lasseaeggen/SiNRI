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


sensor_distance = 1500
sensor_distances = []
is_object_close = False


def receive_sensor():
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


def connect_to_grinder():
    host = '0.0.0.0'
    port = 8080

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            run_demo(s)
    except Exception as e:
        logger.info('Could not connect to remote grinder instance')
        logger.error(traceback.format_exc())


def receive_segment(segment_length, s):
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


def serial_distance(serial_connection):
    return int(serial_connection.readline().strip())


def run_demo(connection):
    meame = meamer.MEAMEr('10.20.92.130')
    SMA_amplitude_threshold = 1e-5
    peak_amplitude_threshold = 7.3e-5
    previous_predictions = []
    previous_object_state = False
    sensor_thread = sthread.StoppableThread(target=receive_sensor)
    sensor_thread.start()

    try:
        while True:
            segment = receive_segment(1000, connection)
            print('A second has passed, {}, {}, {}'.
                  format(abs(np.mean(segment)), np.max(segment), np.mean(previous_predictions)))

            if abs(np.mean(segment))>= SMA_amplitude_threshold or \
               np.max(segment) >= peak_amplitude_threshold:
                prediction = 1.0
            else:
                prediction = 0.0
            previous_predictions.append(prediction)
            previous_predictions = previous_predictions[-10:]

            if (np.mean(previous_predictions) >= 0.5):
                print('seriously epic win')

            if previous_object_state != is_object_close:
                previous_object_state ^= True

                if previous_object_state:
                    meame.start_stim()
                    meame.setup_stim()
                    print('Started remote MEAME stimuli')
                else:
                    meame.stop_stim()
                    print('Stopped remote MEAME stimuli')
    except KeyboardInterrupt as e:
        sensor_thread.stop()


def main():
    connect_to_grinder()


if __name__ == '__main__':
    main()
