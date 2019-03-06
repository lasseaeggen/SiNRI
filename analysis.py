import experiment as expmnt
import channelconverter as chconv
import numpy as np
import matplotlib.pyplot as plt
import lib.detect_peaks as dp


def split(data, sample_rate, ms):
    """
    Splits an array, <data>, into equal sized buckets. Each bucket
    should contain <ms> seconds of data.
    """
    seconds = ms / 1000
    bucket_size = int(seconds * sample_rate)

    # reshape is way faster than array_split.
    buckets = len(data) // bucket_size
    leftover = data[buckets*bucket_size:]
    data = data[:buckets*bucket_size]

    if len(leftover) > 0:
        print('WARNING: Lost leftover of size {}/{} when splitting data'
              .format(len(leftover), len(data)+len(leftover)))

    data = data.reshape(buckets, -1)
    return data


def simple_moving_average(data, N):
    return np.convolve(np.absolute(data), np.ones((N,))/N, mode='valid')


def main():
    ch = chconv.MCSChannelConverter.mcsviz_to_channel[21]
    experiment = expmnt.Experiment('mea_data/1.h5')

    """Example for bucketing data, here plotting the 13th bucket."""
    # (giving the 12th second).
    # ch_data, unit = experiment.get_channel_data(ch)
    # ch_data = split(ch_data, experiment.sample_rate, 1000)

    # plt.plot(ch_data[12])
    # plt.show()

    """Examples for plotting."""
    # experiment.plot_channel(ch, start=11.8, end=12.8)
    # experiment.plot_channels(start=10, end=11)

    """Peak detection example."""
    # ch_data, unit = experiment.get_channel_data(ch)
    # ch_data = split(ch_data, experiment.sample_rate, 1000)
    # ch_data = ch_data[12]
    # dp.detect_peaks(ch_data, show=True)

    """Peak detection example, plotting the amount of peaks of each
    bucket."""
    # ch_data, unit = experiment.get_channel_data(ch)
    # ch_data = split(ch_data, experiment.sample_rate, 1000)
    # threshold = 15*1e-6
    # peaks = [len(dp.detect_peaks(x, mph=threshold)) for x in ch_data]
    # valleys = [len(dp.detect_peaks(x, valley=True, mph=-threshold)) for x in ch_data]
    # plt.plot(peaks)
    # plt.plot(valleys)
    # plt.show()

    """SMA over a given dataset of a window size."""
    # ch_data, unit = experiment.get_channel_data(ch)
    # window_width = 10
    # sma = simple_moving_average(ch_data, window_width)
    # plt.plot(sma)
    # plt.show()


if __name__ == '__main__':
    main()
