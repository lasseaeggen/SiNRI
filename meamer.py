import log
logger = log.get_logger(__name__)

import socket
import struct
import requests
import time
import experiment
from exceptions import UnresponsiveMEAMEError


class MEAMEr(object):
    def __init__(self, address):
        self.data_format = '<i'
        self.address = address
        self.mea_daq_port = 12340
        self.sawtooth_port = 12341
        self.http_address = 'http://' + self.address
        self.http_port = 8888


    def url(self, resource):
        return self.http_address + ':' + str(self.http_port) + resource


    def connection_error(self, e):
        logger.error('Could not connect to remote MEAME server')
        logger.error('{e}'.format(e=e))


    def simple_GET_request(self, url):
        try:
            r = requests.get(self.url(url))
            if r.status_code == 200:
                logger.info('Successful GET request to {url}'.format(url=url))
            else:
                logger.error('Error, GET request to {url} (check MEAME logs)'.format(url=url))
                return
        except Exception as e:
            self.connection_error(e)


    def setup_stim(self):
        self.simple_GET_request('/DSP/stim/setup')


    def start_stim(self):
        self.simple_GET_request('/DSP/stim/start')


    def stop_stim(self):
        self.simple_GET_request('/DSP/stim/stop')


    def flash_dsp(self):
        self.simple_GET_request('/DSP/flash')


    def debug_dsp(self):
        self.simple_GET_request('/DSP/stim/debug')


    def initialize_DAQ(self, sample_rate, segment_length):
        if self.address == 'localhost':
            self.sample_rate = sample_rate
            self.segment_length = segment_length
            return

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
        if self.address == 'localhost':
            return

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
        try:
            self.DAQ_listener.connect((self.address, self.mea_daq_port))
        except ConnectionRefusedError as e:
            logger.error('Remote MEAME is not responding, shutting down')
            raise UnresponsiveMEAMEError('', e)


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

            for i, dp in enumerate(struct.iter_unpack(self.data_format, bsegment_data)):
                segment_data[i] = dp[0] * experiment.Experiment.conversion_constant

            # We are only fetching a select amount of data, so break
            # out when we're done.
            break

        return segment_data


    def recv(self):
        current_channel = 0
        while True:
            data = self.recv_segment()

            if current_channel == 0:
                print(len(data))

            current_channel = (current_channel + 1) % 60
