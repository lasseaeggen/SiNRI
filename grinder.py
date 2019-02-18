import log
logger = log.setup_logger('grinder')


import experiment
import socket
import threading
import time
import requests
import logging
import struct
import json
import traceback
import keyboard


class PlaybackStream(object):
    def __init__(self, client, channel, active_experiment='default'):
        self.client = client
        self.tick_rate = 0.01
        self.channel = channel

        # Initialize the actual experiment
        if active_experiment == 'default':
            active_experiment = 'mea_data/1.h5'
        self.experiment = experiment.Experiment(active_experiment)
        self.change_channel(self.channel)


    # For now each PlaybackStream has a copy of the experiment that it
    # will receive from Server, which may need to be re-done in the
    # future. For now we just choose one experiment on Server startup.
    def change_channel(self, ch):
        self.channel = ch
        self.example_channel_data, self.unit = self.experiment.get_channel_data(ch)
        self.data_per_tick = int(self.experiment.sample_rate * self.tick_rate)
        self.current_tick = 0


    def load_settings(self, settings):
        if 'channel' not in settings:
            raise json.decoder.JSONDecodeError
        self.change_channel(settings['channel'])
        logger.info('Changed channel to channel:{ch}'.format(ch=settings['channel']))


    def get_tick_data(self):
        return self.example_channel_data[self.current_tick*self.data_per_tick:(self.current_tick+1)*self.data_per_tick]


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
        self.meame = MEAMEr()
        self.meame.initialize_DAQ(sample_rate=20000, segment_length=100)
        self.meame.enable_DAQ_listener()


    def change_channel(self, ch):
        self.channel = ch


    def publish(self):
        """
        Receive a whole segment for all channels, and forwards the
        segment for the wanted channel to the client.
        """
        current_channel = 0

        while True:
            data = self.recv_segment()

            if current_channel == self.channel:
                print(data)

            current_channel += 1
            if current_channel == 60:
                return


class Server(object):
    def __init__(self, port, auto_setup=False, sawtooth=False):
        self.host = '0.0.0.0'
        self.port = port
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


class MEAMEr(object):
    def __init__(self):
        self.address = '10.20.92.130'
        self.mea_daq_port = 12340
        self.sawtooth_port = 12341
        self.http_address = 'http://' + self.address
        self.http_port = 8888


    def url(self, resource):
        return self.http_address + ':' + str(self.http_port) + resource


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

            # We succesfully set up the DAQ.
            self.sample_rate = sample_rate
            self.segment_length = segment_length

            # Sleep here to let the DAQ finish setting up. (TODO):
            # This should actually be done by just fetching
            # /DAQ/status.
            time.sleep(0.5)
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


    def enable_DAQ_listener(self):
        self.DAQ_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.DAQ_listener.connect((self.address, self.mea_daq_port))


    def disable_DAQ_listener(self):
        self.DAQ_listener.close()


    def recv_segment(self):
        bytes_received = 0
        bsegment_data = bytearray(b'')
        segment_data = [0]*self.segment_length

        while True:
            data = self.DAQ_listener.recv(self.segment_length*4 - bytes_received)
            bytes_received = bytes_received + len(data)
            bsegment_data.extend(data)

            if (bytes_received != self.segment_length*4):
                continue

            for i, dp in enumerate(struct.iter_unpack('<i', bsegment_data)):
                segment_data[i] = dp

            # We are only fetching a select amount of data, so break
            # out when we're done.
            break

        return segment_data


    def recv(self):
        current_channel = 0
        while True:
            data = self.recv_segment()

            if current_channel == 0:
                print(data)

            current_channel = (current_channel + 1) % 60


    def _recv(self, sample_rate, segment_length):
        """
        Receives actual data acquired on the remote DAQ server. Old
        recv method, which is deprecated now.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.address, self.mea_daq_port))
                channel_data = [bytearray(b'') for x in range(60)]
                segment_data = bytearray(b'')
                current_channel = 0
                bytes_received = 0

                segments = 0
                while True:
                    # Received data points are 32-bit signed integers.
                    data = s.recv(segment_length*4 - bytes_received)
                    bytes_received = bytes_received + len(data)
                    segment_data.extend(data)

                    if (bytes_received != segment_length*4):
                        continue

                    # Just for debugging purposes. Prints size of
                    # buffers every second to see if data acquisition
                    # is somewhat synchronized.
                    if current_channel == 0:
                        if segments == 0:
                            print(len(channel_data[59]))
                        segments = (segments + 1) % (sample_rate // segment_length)

                    # Save the acquired data.
                    channel_data[current_channel].extend(segment_data)

                    # Reset for next channel.
                    segment_data = bytearray(b'')
                    current_channel = (current_channel + 1) % 60
                    bytes_received = 0

                    # After a second, unpack a channel and print it
                    # out for debugging purposes to see whether it's a
                    # sawtooth wave.
                    if len(channel_data[0]) == (sample_rate * 4) * 1:
                        for i in struct.iter_unpack('<i', channel_data[50]):
                            pass
                            # print(i)
        # (TODO): Fix this: Currently other exceptions will remain
        # uncaught for debugging purposes.
        except ConnectionError as e:
            logger.error('Could not listen to remote MEAME DAQ server (sawtooth)')
            logger.error(e)


def main(args):
    if args.live:
        meame = MEAMEr()
        # meame.initialize_DAQ(sample_rate=20000, segment_length=100)
        # meame.enable_DAQ_listener()
        # meame.recv()
    elif args.playback:
        try:
            server = Server(8080,
                            auto_setup=args.auto_setup,
                            sawtooth=args.sawtooth)
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
    parser.add_argument('--channel', help='Specify which of the MEA output channels is wanted')

    args = parser.parse_args()
    main(args)
