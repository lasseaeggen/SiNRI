import experiment as expmnt
import channelconverter as chconv


def main():
    ch = chconv.MCSChannelConverter.mcsviz_to_channel[21]
    experiment = expmnt.Experiment('mea_data/1.h5')
    experiment.plot_channel(ch, start=11.8, end=12.8)


if __name__ == '__main__':
    main()
