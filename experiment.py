import log
logger = log.get_logger(__name__)

from McsPy import McsData
import McsPy


class Experiment(object):
    def __init__(self, h5_file):
        self.data = McsData.RawData(h5_file)
        McsData.VERBOSE = False
        logger.info('Reading analog streams from {f}'.format(f=h5_file))
        self.stream = self.data.recordings[0].analog_streams[0]
        McsData.VERBOSE = True
        self.sample_rate = self.stream.channel_infos[0].sampling_frequency.magnitude
        self.channels = len(self.stream.channel_infos)


    def get_channel_data(self, channel):
        return self.stream.get_channel_in_range(channel, 0, self.stream.channel_data.shape[1])


    def get_channel_in_range(self, channel, i, j):
        return self.stream.get_channel_in_range(channel, i, j)
