import experiment as expmnt


def main():
    experiment = expmnt.Experiment('mea_data/1.h5')
    experiment.plot_channel(0)


if __name__ == '__main__':
    main()
