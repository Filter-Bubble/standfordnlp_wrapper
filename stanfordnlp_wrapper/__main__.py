import logging
import argparse
import sys
import io

from . import parse, __version__

try:
    # python3: sys.stdin.buffer contains the 'bytes'
    input_file = sys.stdin.buffer
except AttributeError:
    # python2: sys.stdin contains bytes (aka 'str)
    input_file = sys.stdin
user_max = None

parser = argparse.ArgumentParser(description='Morphosyntactic parser based on Stanfordnlp')
parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
parser.add_argument('-V', '--version', action='version', version="{} ({})".format(__name__, __version__))


args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                    format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

# Mute output
stdout = io.StringIO()
sys.stdout = stdout
in_obj = parse(input_file)
sys.stdout = sys.__stdout__
in_obj.dump()
