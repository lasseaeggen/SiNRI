import log
logger = log.get_logger(__name__)

import experiment
import socket
import struct
import time


class MEAMEMock(object):
    def __init__(self, port):
        self.host = '0.0.0.0'
        self.port = port
        self.experiment = experiment.Experiment('mea_data/1.h5')
        self.tick_rate = 0.01
        self.ticks_per_sec = int(1 / self.tick_rate)
        self.data_per_tick = int(self.experiment.sample_rate * self.tick_rate)
        self.data = {}

        # Only fetch a small amount of data that will be replayed. We
        # are mostly just interested in having something that mocks
        # MEAME at all for testing purposes.
        logger.info('Initializing MEAME mock by reading experiment data')
        self.seconds = 15
        self.playback_length = int(self.seconds * self.experiment.sample_rate)
        for i in range(60):
            logger.info('Channel {i} read'.format(i=i))
            self.data[i] = self.experiment.get_channel_in_range(i, 0, self.playback_length)[0]


    def run(self):
        while True:
            try:
                self.listen()
            except KeyboardInterrupt:
                return


    def listen(self):
        logger.info('Setting up MEAME mock socket, awaiting connections')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)

        client, addr = s.accept()
        logger.info('Received connection from {addr}'.format(addr=addr))
        tick = 0
        prev_time = time.perf_counter()
        try:
            while True:
                for i in range(60):
                    data = [int(x / experiment.Experiment.conversion_constant) for x in
                            self.data[i][tick*self.data_per_tick:(tick+1)*self.data_per_tick]]
                    client.send(struct.pack('<{}i'.format(len(data)), *data))
                tick = (tick + 1) % (self.seconds * self.ticks_per_sec)

                # To keep a steady pace, we need to sleep only a given
                # amount of time, as it is unlikely that each
                # iteration takes exactly the same amount of time.
                diff = time.perf_counter() - prev_time
                sleep_time = min(max(self.tick_rate - diff, 0), self.tick_rate)
                prev_time = time.perf_counter()
                time.sleep(sleep_time)
        except (KeyboardInterrupt, SystemExit,
                ConnectionResetError, BrokenPipeError):
            client.close()
            logger.info('Shutdown request detected, shutting down gracefully')
            s.shutdown(socket.SHUT_RDWR)


def main():
    mock = MEAMEMock(12340)
    mock.run()


if __name__ == '__main__':
    main()
