import log
logger = log.get_logger(__name__)

import meamer


def main(args):
    meame = meamer.MEAMEr('10.20.92.130')

    if args.setup:
        meame.setup_stim()
    if args.start:
        meame.start_stim()
        meame.setup_stim()
    elif args.stop:
        meame.stop_stim()
    elif args.flash:
        meame.flash_dsp()
    elif args.debug:
        meame.debug_dsp()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Grinder - the minimal MEAME communicator')

    parser.add_argument('--setup', help='Setup DSP for MEA stimuli', action='store_true')
    parser.add_argument('--start', help='Start MEA stimuli', action='store_true')
    parser.add_argument('--stop', help='Stop MEA stimuli', action='store_true')
    parser.add_argument('--flash', help='Flash DSP, should be done after power cycle', action='store_true')
    parser.add_argument('--debug', help='Send debug request to MEAME, prints in MEAME console', action='store_true')

    args = parser.parse_args()
    main(args)
