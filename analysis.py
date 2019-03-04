import experiment as expmnt


def main():
    experiment = expmnt.Experiment('mea_data/1.h5')
    experiment.plot_channel(0, start=11.8, end=12.8)


if __name__ == '__main__':
    main()
