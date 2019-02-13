import socket
import logging
import traceback
import struct


# Set up a global (root) logger for now (yuck!). Fix this when things
# are split into modules.
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('grinder')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def receive_from_matlab():
    host = '0.0.0.0'
    port = 8081
    mea_threshold = 1e-5
    sawtooth_threshold = 2

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(5)
        (client, addr) = s.accept()
        client.settimeout(60)
    except Exception as e:
        logger.info('Received connection from {addr}'.format(addr=addr))
        logger.error(traceback.format_exc())

    try:
        while True:
            data = client.recv(1024)
            for i in struct.iter_unpack('<f', data):
                if i[0] > mea_threshold:
                    print('EPIC WIN', end='\r')
                else:
                    print('        ', end='\r')
    except (BrokenPipeError, OSError):
        logger.info('Closing connection from {addr} (broken pipe)'.format(addr=addr))
        client.close()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutdown request detected, shutting down gracefully')
        client.close()
        s.shutdown(socket.SHUT_RDWR)


def main():
    receive_from_matlab()


if __name__ == '__main__':
    main()
