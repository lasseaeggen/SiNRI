from McsPy import McsData
import socket
import threading
import time
import pickle
import requests
import logging


# Set up a global (root) logger for now (yuck!). Fix this when things
# are split into modules.
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('grinder')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


class Experiment(object):
    def __init__(self, h5_file):
        self.data = McsData.RawData(h5_file)
        self.stream = self.data.recordings[0].analog_streams[0]
        self.sample_rate = self.stream.channel_infos[0].sampling_frequency.magnitude
        self.channels = len(self.stream.channel_infos)


    def get_channel_data(self, ch):
        return self.stream.get_channel_in_range(ch, 0, self.stream.channel_data.shape[1])


class Server(object):
    def __init__(self, port):
        self.host = '0.0.0.0'
        self.port = port
        self.experiment = Experiment('mea_data/1.h5')
        self.example_channel_data, self.unit = self.experiment.get_channel_data(0)

        # Set up playback settings.
        self.tick_rate = 0.01
        self.data_per_tick = int(self.experiment.sample_rate * self.tick_rate)


    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.bind((self.host, self.port))
            logger.info('Server started on {host}:{port}'.format(host=self.host, port=self.port))
        except Exception as e:
            logger.error('Could not bind to port {port}'.format(port=self.port))
            logger.error('{e}'.format(e=e))
            return

        try:
            self.socket.listen(5)
            while True:
                (client, addr) = self.socket.accept()
                client.settimeout(60)
                logger.info('Received connection from {addr}'.format(addr=addr))
                threading.Thread(target=self.handle_client, args=(client, addr)).start()
        except (KeyboardInterrupt, SystemExit):
            logger.info('Shutdown request detected, shutting down gracefully')
            self.socket.shutdown(socket.SHUT_RDWR)


    def handle_client(self, client, addr):
        tick = 0

        while True:
            try:
                data = self.example_channel_data[tick*self.data_per_tick:(tick+1)*self.data_per_tick]
                client.send(pickle.dumps(data))
                tick = tick + 1
                time.sleep(self.tick_rate)
            except (BrokenPipeError, OSError):
                logger.info('Closing connection from {addr}'.format(addr=addr))
                client.close()
                break
            except Exception as e:
                logger.error('Error handling connection from {addr}'.format(addr=addr))
                logger.error('{e}'.format(e=e))
                client.close()
                break


class MEAMEr(object):
    def __init__(self):
        self.address = 'http://10.20.92.130'
        self.port = 8888


    def url(self, resource):
        return self.address + ':' + str(self.port) + resource


    def connection_error(self, e):
        logger.error('Could not connect to remote MEAME server')
        logger.error('{e}'.format(e=e))


    def initialize_DAQ(self, sample_rate, segment_length):
        try:
            r = requests.post(self.url('/DAQ/connect'), json = {
                'samplerate': sample_rate,
                'segmentLength': segment_length,
            })

            if r.status_code == 200:
                logger.info('Successfully set up MEAME DAQ server')
            else:
                logger.info('DAQ connection failed (malformed request?)')
                return

            r = requests.get(self.url('/DAQ/start'))
            if r.status_code == 200:
                logger.info('Successfully started DAQ server')
            else:
                logger.error('Could not start remote DAQ server')
                return
        except Exception as e:
            self.connection_error(e)


    def stop_DAQ(self):
        """
        Warning: stopping the DAQ server is not implemented in
        MEAME. This method will in practice achieve nothing at all.
        """
        try:
            r = requests.get(self.url('/DAQ/stop'))
            if r.status_code == 200:
                logger.info('Successfully stopped DAQ server')
            else:
                logger.error('Could not stop remote DAQ server (status code 500)')
                return
        except Exception as e:
            self.connection_error(e)


def main():
    """For setting up a server for an experiment."""
    # server = Server(8080)
    # server.listen()

    """For setting up remote MEAME and receiving data."""
    meame = MEAMEr()
    meame.initialize_DAQ(sample_rate=20000, segment_length=100)


if __name__ == '__main__':
    main()
