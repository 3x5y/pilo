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
    try:
        f()
    except FatalError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)