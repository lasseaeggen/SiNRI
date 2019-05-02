import log
logger = log.get_logger(__name__)

from McsPy import McsData
import McsPy
import logging
import matplotlib.pyplot as plt
import numpy as np


class Experiment(object):
    """
    Wraps recordings from MEA with nice-to-have methods for things
    such as extracting data.
    """
    # Statically set for all experiment objets.
    conversion_constant = 5.9605e-08

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
        """
        Returns the full range of data from a single channel.
        """
        return self.stream.get_channel_in_range(channel, 0, self.stream.channel_data.shape[1])


    def get_channel_in_range(self, channel, i, j):
        """
        Returns channel data from sample <i> to sample <j>.
        """
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
        """
        Outputs information about the corresponding experiment.
        """
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


    def get_channel_plot_data(self, ch, start=0, end=0):
        # Fetch the wanted channel information.
        ch_info = self.stream.channel_infos[ch]
        ch_data = self.stream.channel_data[ch]

        # How much data do we want to plot (all of it for now)?
        if start:
            start = int(start * self.sample_rate)
        if end:
            end = int(end * self.sample_rate)
        else:
            end = ch_data.shape[0]

        # Get x-axis.
        timestamps, unit = self.stream.get_channel_sample_timestamps(ch, start, end)
        timestamps = McsPy.ureg.convert(timestamps, unit, 'seconds')

        # Get y-axis.
        data, unit = self.stream.get_channel_in_range(ch, start, end)
        data = McsPy.ureg.convert(data, unit, 'microvolt')

        return timestamps, data


    def plot_channel(self, ch, start=0, end=0, ylim=100):
        """
        Plots a given channel within a recording. start and stop are
        used to specify the interval that is to be used. ylim
        specifies y-axis range in microvolts.
        """
        # Initialize plot(s).
        fig, axes = plt.subplots(1, 1, figsize=(15, 10))
        fig.suptitle(self.filename + ' - Channel: {}'.format(ch))

        axes = np.atleast_1d(axes)
        axes = axes.flatten()
        ax = axes[0]
        ax.set_ylabel('μV')
        ax.set_xlabel('Time')
        ax.set_ylim(-ylim, ylim)

        timestamps, data = self.get_channel_plot_data(ch, start, end)
        ax.plot(timestamps, data, color='#EB9904')
        plt.show()


    def plot_channels(self, start=0, end=0, ylim=100):
        """
        Plots all the channels within a recording. start and stop are
        used to specify the interval that is to be used. ylim
        specifies y-axis range in microvolts.
        """
        # Initialize plot(s).
        fig, axes = plt.subplots(6, 10, figsize=(15, 10))
        fig.suptitle(self.filename)

        axes = np.atleast_1d(axes)
        axes = axes.flatten()

        for ch in range(60):
            print('plot_channels: Reading channel: {}'.format(ch))
            ax = axes[ch]
            ax.set_title(ch)
            ax.set_ylabel('μV')
            ax.set_xlabel('Time')
            ax.set_ylim(-ylim, ylim)

            timestamps, data = self.get_channel_plot_data(ch, start, end)
            ax.plot(timestamps, data, color='#EB9904')

        plt.show()
