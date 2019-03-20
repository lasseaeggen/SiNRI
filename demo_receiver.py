import log
logger = log.get_logger(__name__)


import socket
import traceback
import struct
import numpy as np
import serial
import sthread
import time


sensor_distance = 1500
def receive_sensor():
    global sensor_distance
    with serial.Serial('/dev/ttyUSB5') as ser:
        while True:
            sensor_distance = serial_distance(ser)

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
    amplitude_threshold = 1e-5
    sensor_thread = sthread.StoppableThread(target=receive_sensor)
    sensor_thread.start()

    try:
        while True:
            segment = receive_segment(10000, connection)
            print('A second has passed, {}'.format(abs(np.mean(segment))))
            if abs(np.mean(segment))>= amplitude_threshold:
                print('epic win')

            if sensor_distance < 100:
                print('you are very close >:(')
    except KeyboardInterrupt as e:
        sensor_thread.stop()


def main():
    connect_to_grinder()


if __name__ == '__main__':
    main()
