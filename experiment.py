import log
logger = log.get_logger(__name__)

from McsPy import McsData
import McsPy
import logging


class Experiment(object):
    def __init__(self, h5_file):
        # McsData a bunch of garbage (hopefully _only_ garbage).
        McsData.VERBOSE = False

        # Silence the logging for this, as McsPy will spew _warnings_
        # we don't care about.
        logging.getLogger('pint').setLevel(logging.ERROR)

        logger.info('Reading analog streams from {f}'.format(f=h5_file))
        self.filename = h5_file
        self.data = McsData.RawData(h5_file)
        self.stream = self.data.recordings[0].analog_streams[0]
        self.sample_rate = self.stream.channel_infos[0].sampling_frequency.magnitude
        self.channels = len(self.stream.channel_infos)
        self.current_second = 0
        self.seconds_per_step = 15
        self.current_data = [[]]*60


    def get_channel_data(self, channel):
        return self.stream.get_channel_in_range(channel, 0, self.stream.channel_data.shape[1])


    def get_channel_in_range(self, channel, i, j):
        return self.stream.get_channel_in_range(channel, i, j)


    def get_tick_data(self):
        """
        Returns a second of samples (i.e. sample_rate amount of
        sample). Also ticks the current second.
        """
        start = int(self.current_second * self.sample_rate)
        stop = int((self.current_second+self.seconds_per_step) * self.sample_rate)
        self.current_second += self.seconds_per_step

        for ch in range(60):
            self.current_data[ch] = self.get_channel_in_range(ch, start, stop)[0]
        return self.current_data


    def info(self):
        print('Experiment INFO: {}'.format(self.filename))
        recording = self.data.recordings[0]

        # A single hdf5-file may contain more than one recording.
        for i, recording in self.data.recordings.items():
            print('  Recording {}'.format(i))
            print('  Duration  {}s'.format(recording.duration_time.to('seconds').magnitude))

            # Print information regarding all the streams within the
            # current recording.
            for j, stream in recording.analog_streams.items():
                stream_format = stream.channel_data.shape
                print('    Stream {} format:'.format(j))
                print('      {} channels, {} samples per channel, {} hertz:'.
                      format(stream_format[0], stream_format[1], self.sample_rate))

                # Print information regarding all the channels within
                # the analog stream.
                print('    Channels in stream:')
                for k, channel in stream.channel_infos.items():
                    info = channel.info
                    print('      ID: {:3}   Label: {:3}   EG: {}'.format(
                          info['ChannelID'],
                          info['Label'],
                          info['ElectrodeGroup']))
