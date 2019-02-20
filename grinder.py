import log
logger = log.setup_logger('grinder')

import experiment
import meamer
import socket
import threading
import time
import requests
import logging
import struct
import json
import traceback
import keyboard


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
        # are mostly just interesting in having something that mocks
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
        try:
            while True:
                for i in range(60):
                    data = self.data[i][tick*self.data_per_tick:(tick+1)*self.data_per_tick]
                    client.send(struct.pack('{}f'.format(len(data)), *data))
                tick = (tick + 1) % (self.seconds * self.ticks_per_sec)
                time.sleep(self.tick_rate)
        except (KeyboardInterrupt, SystemExit,
                ConnectionResetError, BrokenPipeError):
            client.close()
            logger.info('Shutdown request detected, shutting down gracefully')
            s.shutdown(socket.SHUT_RDWR)


class PlaybackStream(object):
    def __init__(self, client, channel, active_experiment='default'):
        self.client = client
        self.tick_rate = 0.01
        self.channel = channel

        # Initialize the actual experiment
        if active_experiment == 'default':
            active_experiment = 'mea_data/1.h5'
        self.experiment = experiment.Experiment(active_experiment)
        self.data_per_tick = int(self.experiment.sample_rate * self.tick_rate)
        self.change_channel(self.channel)


    # For now each PlaybackStream has a copy of the experiment that it
    # will receive from Server, which may need to be re-done in the
    # future.
    def change_channel(self, ch):
        self.channel = ch
        self.example_channel_data, self.unit = self.experiment.get_channel_data(ch)
        self.current_tick = 0


    def load_settings(self, settings):
        if 'channel' not in settings:
            raise json.decoder.JSONDecodeError
        self.change_channel(settings['channel'])
        logger.info('Changed channel to channel:{ch}'.format(ch=settings['channel']))


    def get_tick_data(self):
        return self.example_channel_data[self.current_tick*self.data_per_tick
                                         :(self.current_tick+1)*self.data_per_tick]


    def tick(self):
        self.current_tick = self.current_tick + 1
        time.sleep(self.tick_rate)


    def publish(self):
        data = self.get_tick_data()
        self.client.send(struct.pack('{}f'.format(len(data)), *data))


    def close(self):
        self.client.close()


class LiveStream(object):
    def __init__(self, client, channel):
        self.client = client
        self.channel = channel
        self.meame = meamer.MEAMEr()
        self.meame.initialize_DAQ(sample_rate=10000, segment_length=100)
        self.meame.enable_DAQ_listener()


    def change_channel(self, ch):
        self.channel = ch


    def tick(self):
        return


    def publish(self):
        """
        Receive a whole segment for all channels, and forwards the
        segment for the wanted channel to the client.
        """
        current_channel = 0

        while True:
            data = self.meame.recv_segment()

            if current_channel == self.channel:
                self.client.send(struct.pack('{}f'.format(len(data)), *data))

            current_channel += 1
            if current_channel == 60:
                return


    def close(self):
        self.client.close()
        self.meame.disable_DAQ_listener()


class Server(object):
    live = False

    def __init__(self, port, auto_setup=False, sawtooth=False):
        self.host = '0.0.0.0'
        self.port = port
        self.live = Server.live
        self.auto_setup = auto_setup
        self.sawtooth = sawtooth


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


    def forward_channel(self, ch, addr, port):
        """
        Connects directly to a remote client to forward an experiment
        channel.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((addr, port))
            stream = PlaybackStream(s, ch)
            while True:
                try:
                    stream.publish()
                    stream.tick()
                except (BrokenPipeError, OSError):
                    logger.info('Closing connection to {addr}'.format(addr=addr))
                    client.close()
                    break


    def setup_playback_stream(self, client):
        if self.auto_setup:
            return PlaybackStream(client, 0, 'default')
        else:
            try:
                settings_json = client.recv(2048)
                settings = json.loads(settings_json.decode('utf-8'))
            except (json.decoder.JSONDecodeError, KeyError) as e:
                logger.info('Received malformed JSON from {addr}, disconnecting'.format(addr=addr))
                return None

            try:
                return PlaybackStream(client, settings['channel'], settings['experiment'])
            except KeyError as e:
                logger.info('Received malformed settings from {addr}, disconnecting'.format(addr=addr))
                stream.close()
                return None


    def setup_live_stream(self, client):
        return LiveStream(client, 0)


    def handle_client(self, client, addr):
        if self.live:
            stream = self.setup_live_stream(client)
        else:
            stream = self.setup_playback_stream(client)
        while True:
            try:
                if self.sawtooth:
                    i = stream.current_tick % 100
                    if keyboard.is_pressed('y'):
                        data = [i for x in range(100)]
                    else:
                        data = [0 for x in range(100)]
                    client.send(struct.pack('{}f'.format(len(data)), *data))
                else:
                    stream.publish()
                stream.tick()
            except (BrokenPipeError, OSError):
                logger.info('Closing connection from {addr} (broken pipe)'.format(addr=addr))
                client.close()
                break
            except Exception as e:
                logger.error('Error handling connection from {addr}'.format(addr=addr))
                logger.error('{e}'.format(e=e))
                logger.error(traceback.format_exc())
                client.close()
                break


def main(args):
    # Static member of the MEAMEr class for now, we should perhaps
    # refactor this into setting a complete configuration on startup
    # instead.
    if args.connect_mock:
        meamer.MEAMEr.mock = True

    if args.live:
        Server.live = True

    if args.meame:
        mock = MEAMEMock(12340)
        mock.run()
    else:
        try:
            server = Server(8080, auto_setup=args.auto_setup, sawtooth=args.sawtooth)
            server.listen()
        except Exception as e:
            logger.info('Unexpected event, shutting down gracefully')
            server.socket.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Grinder - the minimal MEAME communicator')

    parser.add_argument('--live', help='Acquire live data from remote MEAME DAQ server', action='store_true')
    parser.add_argument('--playback', help='Replay and serve experiments from hd5 files', action='store_true')
    parser.add_argument('--meame', help='Take the place of MEAME, sending mock data', action='store_true')
    parser.add_argument('--auto-setup', help='Serve playback directly without setup', action='store_true')
    parser.add_argument('--sawtooth', help='Set server to auto generate sawtooth waves', action='store_true')
    parser.add_argument('--channel', help='Specify which of the MEA output channels is wanted')
    parser.add_argument('--connect-mock', help='Connect to a mock DAQ server, no setup possible', action='store_true')

    args = parser.parse_args()
    main(args)
