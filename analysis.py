import experiment as expmnt
import matplotlib.pyplot as plt


def main():
    experiment = expmnt.Experiment('mea_data/1.h5')
    experiment.info()


if __name__ == '__main__':
    main()
