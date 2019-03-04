import experiment as expmnt
import channelconverter as chconv
import numpy as np
import matplotlib.pyplot as plt


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


def main():
    ch = chconv.MCSChannelConverter.mcsviz_to_channel[21]
    experiment = expmnt.Experiment('mea_data/1.h5')

    # Example for bucketing data, here plotting the 13th bucket
    # (giving the 12th second).
    # ch_data, unit = experiment.get_channel_data(ch)
    # ch_data = split(ch_data, experiment.sample_rate, 1000)

    # plt.plot(ch_data[12])
    # plt.show()

    # Examples for plotting.
    # experiment.plot_channel(ch, start=11.8, end=12.8)
    # experiment.plot_channels(start=10, end=11)


if __name__ == '__main__':
    main()
