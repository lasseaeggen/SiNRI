import log
logger = log.get_logger(__name__)

import meamer


def main(args):
    meame = meamer.MEAMEr()

    if args.start:
        meame.setup_stim()
        meame.enable_stim()
    elif args.stop:
        meame.disable_stim()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Grinder - the minimal MEAME communicator')

    parser.add_argument('--start', help='Start MEA stimuli', action='store_true')
    parser.add_argument('--stop', help='Stop MEA stimuli', action='store_true')

    args = parser.parse_args()
    main(args)
