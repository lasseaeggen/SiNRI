import log
logger = log.get_logger(__name__)

import meamer


def main(args):
    meame = meamer.MEAMEr()

    if args.setup:
        meame.setup_stim()
    if args.start:
        meame.enable_stim()
    elif args.stop:
        meame.disable_stim()
    elif args.flash:
        meame.flash_dsp()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Grinder - the minimal MEAME communicator')

    parser.add_argument('--setup', help='Setup DSP for MEA stimuli', action='store_true')
    parser.add_argument('--start', help='Start MEA stimuli', action='store_true')
    parser.add_argument('--stop', help='Stop MEA stimuli', action='store_true')
    parser.add_argument('--flash', help='Flash DSP, should be done after power cycle', action='store_true')

    args = parser.parse_args()
    main(args)
