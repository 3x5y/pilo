import logging
import os
import sys


class PiloException(Exception):
    pass


class PiloError(PiloException):
    pass


class FatalError(PiloError):
    pass


def fatal(msg):
    raise FatalError(msg)


def run_main(f):
    log_level_attr = os.environ.get('PILO_LOG_LEVEL', 'WARNING')
    log_level = logging.getLevelName(log_level_attr)
    logging.basicConfig(level=log_level, format='%(levelname)s %(message)s')
    try:
        f()
    except FatalError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
