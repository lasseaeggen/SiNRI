import log
logger = log.get_logger(__name__)

import experiment as expmnt
import channelconverter as chconv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import lib.detect_peaks as dp
import time
import scipy
from scipy.signal import stft, get_window
from sklearn.linear_model import Ridge


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
    """
    Convolves a SMA kernel of widow size <N> over the data stream
    contained in <data>.
    """
    return np.convolve(np.absolute(data), np.ones((N,))/N, mode='valid')


def spectral_analysis(data):
    """
    A simple analysis for how to do spectral analysis on a stream,
    <data>, in real time. Also illustrates how plots can be updated
    live.
    """
    sample_rate = 10000
    seconds = 35
    data_length = seconds * sample_rate
    seg_length = 500
    noverlap = 0.8
    segments = data_length // (seg_length*(1-noverlap))
    segments_per_second = segments // seconds
    num_buckets = 50

    f, t, Zxx = stft(data[:data_length], fs=10000, window='hamming',
                     nperseg=seg_length, noverlap=seg_length*noverlap)
    f = f[:num_buckets]
    Zxx = np.abs(Zxx[:num_buckets, :])

    # Normal method of doing this -- looks a slight bit different with
    # vmin, vmax, cmap.
    # fig = plt.pcolormesh(t, f, np.abs(Zxx))
    # plt.show()

    # Main figure.
    fig = plt.figure(1)

    # Axes of imshow for raw data.
    ax_raw = fig.add_subplot(211)
    im_raw, = ax_raw.plot(data[:data_length], color='#EB9904')

    # Axes of imshow for spectrum.
    ax_spec = fig.add_subplot(212)
    im_spec = ax_spec.imshow(Zxx, extent=[0, t[-1], 0, f[-1]],
                             aspect='auto', origin='lowest', cmap='jet')


    pause = False
    def on_click(event):
        if event.key == 'p':
            nonlocal pause
            pause ^= True


    ticks = 0
    def update_data(n):
        if pause:
            return

        nonlocal ticks
        ticks += 1

        # Update raw plot.
        start = int(ticks/10 * sample_rate)
        end = int((ticks+30)/10 * sample_rate)
        ax_raw.clear()
        ax_raw.set_ylim(-100, 100)
        ax_raw.plot(data[start:end], color='#EB9904')

        # Update spectrogram.
        start = int(ticks * segments_per_second*0.1)
        end = int((ticks+30) * segments_per_second*0.1)
        im_spec.set_extent([ticks/10, (ticks+30)/10, 0, f[-1]])
        im_spec.set_data(Zxx[:, start:end])


    fig.canvas.mpl_connect('key_press_event', on_click)
    ani = animation.FuncAnimation(fig, update_data, interval=100, blit=False, repeat=False)
    plt.show()


experiment_fp = 'mea_data/1.h5'

# Only used such that you don't have to keep passing the channel and
# experiment to all these analysis functions, as they all take the
# same types of arguments.
def pass_channel(func):
    """
    A simple decorator to use on the examples contained in this
    file. This will automatically pass a channel and experiment to
    such analysis functions.
    """
    def analysis_func():
        ch = chconv.MCSChannelConverter.mcsviz_to_channel[21]
        experiment = expmnt.Experiment(experiment_fp)
        func(ch, experiment)
    return analysis_func


@pass_channel
def bucketing_example(ch, experiment):
    """
    Example for bucketing data, here plotting the 13th bucket (giving
    the 12th second).
    """
    ch_data, unit = experiment.get_channel_data(ch)
    ch_data = split(ch_data, experiment.sample_rate, 1000)

    plt.plot(ch_data[12])
    plt.show()


@pass_channel
def plotting_example(ch, experiment):
    """
    Examples for plotting.
    """
    experiment.plot_channel(ch, start=11.8, end=12.8)
    # experiment.plot_channels(start=10, end=11)


@pass_channel
def peak_detection_example(ch, experiment):
    """
    Peak detection example.
    """
    ch_data, unit = experiment.get_channel_data(ch)
    ch_data = split(ch_data, experiment.sample_rate, 1000)
    ch_data = ch_data[12]
    dp.detect_peaks(ch_data, show=True)


@pass_channel
def peak_detection_summary_example(ch, experiment):
    """
    Peak detection example, plotting the amount of peaks of each
    bucket.
    """
    ch_data, unit = experiment.get_channel_data(ch)
    ch_data = split(ch_data, experiment.sample_rate, 1000)
    threshold = 15*1e-6
    peaks = [len(dp.detect_peaks(x, mph=threshold)) for x in ch_data]
    valleys = [len(dp.detect_peaks(x, valley=True, mph=-threshold)) for x in ch_data]
    plt.plot(peaks)
    plt.plot(valleys)
    plt.show()


@pass_channel
def simple_moving_average_example(ch, experiment):
    """
    SMA over a given dataset of a window size.
    """
    ch_data, unit = experiment.get_channel_data(ch)
    window_width = 10
    sma = simple_moving_average(ch_data, window_width)
    plt.plot(sma)
    plt.show()


@pass_channel
def ridge_regression_example(ch, experiment):
    """
    Try to do ridge regression over some training data. Does not do
    anything at all for now.
    """
    ch_data, unit = experiment.get_channel_data(0)
    f, t, Zxx = stft(ch_data, fs=10000, window='hamming',
                      nperseg=500, noverlap=500*0.8)
    samples = np.transpose(np.abs(Zxx))
    samples_per_sec = round(len(ch_data) / samples.shape[0])

    positives = samples[12*100:int(12*100+0.6*100)]
    negatives = samples[:60]

    print(positives, negatives)
    print(np.max(positives), np.max(negatives))

    # Create training data.
    x_train = np.append(positives, negatives, axis=0)
    y_train = [True for x in range(60)] + [False for x in range(60)]

    # Fit model.
    clf = Ridge(alpha=1.0)
    clf.fit(x_train, y_train)
    clf.predict(samples[12*100].reshape(-1, 1).T)


@pass_channel
def spectral_analysis_example(ch, experiment):
    """
    Spectral analysis.
    """
    ch_timestamps, ch_data = experiment.get_channel_plot_data(0)
    spectral_analysis(ch_data)


def main():
    spectral_analysis_example()


if __name__ == '__main__':
    main()
