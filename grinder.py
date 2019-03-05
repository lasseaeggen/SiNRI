import log
logger = log.get_logger(__name__)

import channelconverter as chconv
import experiment
import meamer
import socket
import threading
import time
import requests
import struct
import json
import traceback
import keyboard


class Stream(object):
    def __init__(self):
        self.reflect = False


    def enable_reflector_mode(self):
        self.reflect = True


    def disable_reflector_mode(self):
        self.reflect = False


class PlaybackStream(Stream):
    def __init__(self, client, channel, segment_length=100, active_experiment='default'):
        super().__init__()
        self.client = client
        self.tick_rate = 0.01
        self.channel = channel
        self.segment_length = segment_length
        self.available_ticks = 0

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


    def load_settings(self, settings):
        if 'channel' not in settings:
            raise json.decoder.JSONDecodeError
        self.change_channel(settings['channel'])
        logger.info('Changed channel to channel:{ch}'.format(ch=settings['channel']))


    def get_tick_data(self):
        self.data = self.experiment.get_tick_data()
        self.available_ticks = len(self.data[0]) // self.segment_length
        self.data_tick_length = self.available_ticks


    def tick(self):
        self.available_ticks -= 1
        time.sleep(self.tick_rate)


    def publish(self):
        if self.available_ticks == 0:
            self.get_tick_data()

        start = (self.data_tick_length - self.available_ticks) * self.segment_length
        stop = start + self.segment_length
        for ch in range(60):
            data = self.data[ch][start:stop]
            if self.reflect:
                self.client.send(struct.pack('{}f'.format(len(data)), *data))
            elif ch == self.channel:
                self.client.send(struct.pack('{}f'.format(len(data)), *data))


    def close(self):
        self.client.close()


class LiveStream(Stream):
    def __init__(self, client, channel):
        super().__init__()
        self.client = client
        self.channel = channel
        self.reflect =  False
        self.meame = meamer.MEAMEr()
        self.meame.initialize_DAQ(sample_rate=10000, segment_length=1000)
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

            if self.reflect:
                self.client.send(struct.pack('{}f'.format(len(data)), *data))
            elif current_channel == self.channel:
                self.client.send(struct.pack('{}f'.format(len(data)), *data))

            current_channel += 1
            if current_channel == 60:
                return


    def close(self):
        self.client.close()
        self.meame.disable_DAQ_listener()


class Server(object):
    live = False

    def __init__(self, port, auto_setup=False, sawtooth=False, reflect=False):
        self.host = '0.0.0.0'
        self.port = port
        self.live = Server.live
        self.auto_setup = auto_setup
        self.sawtooth = sawtooth
        self.reflect = reflect


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
            return PlaybackStream(client, 0, segment_length=100, active_experiment='default')
        else:
            try:
                settings_json = client.recv(2048)
                settings = json.loads(settings_json.decode('utf-8'))
            except (json.decoder.JSONDecodeError, KeyError) as e:
                logger.info('Received malformed JSON from {addr}, disconnecting'.format(addr=addr))
                return None

            try:
                return PlaybackStream(client, settings['channel'], segment_length=100,
                                      active_experiment=settings['experiment'])
            except KeyError as e:
                logger.info('Received malformed settings from {addr}, disconnecting'.format(addr=addr))
                stream.close()
                return None


    def setup_live_stream(self, client):
        channel = chconv.MCSChannelConverter.mcsviz_to_channel[22]
        return LiveStream(client, channel)


    def handle_client(self, client, addr):
        if self.live:
            stream = self.setup_live_stream(client)
        else:
            stream = self.setup_playback_stream(client)

        if self.reflect:
            stream.enable_reflector_mode()

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

    try:
        server = Server(8080,
                        auto_setup=args.auto_setup,
                        sawtooth=args.sawtooth,
                        reflect=args.reflect)
        server.listen()
    except Exception as e:
        logger.info('Unexpected event, shutting down gracefully')
        server.socket.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Grinder - the minimal MEAME communicator')

    parser.add_argument('--live', help='Acquire live data from remote MEAME DAQ server', action='store_true')
    parser.add_argument('--playback', help='Replay and serve experiments from hd5 files', action='store_true')
    parser.add_argument('--auto-setup', help='Serve playback directly without setup', action='store_true')
    parser.add_argument('--sawtooth', help='Set server to auto generate sawtooth waves', action='store_true')
    parser.add_argument('--connect-mock', help='Connect to a mock DAQ server, no setup possible', action='store_true')
    parser.add_argument('--reflect', help='Reflect the stream data «as-is», without demultiplexing channels', action='store_true')

    args = parser.parse_args()
    main(args)
