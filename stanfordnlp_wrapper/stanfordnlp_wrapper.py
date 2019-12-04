# -*- coding: utf-8 -*-
import logging

from KafNafParserPy import KafNafParser
from lxml.etree import XMLSyntaxError
from io import BytesIO
import sys

logger = logging.getLogger(__name__)


def get_naf(input_file):

    input = input_file.read()
    try:
        naf = KafNafParser(BytesIO(input))
    except XMLSyntaxError:
        input = input.decode("utf-8")
        if "<NAF" in input and "</NAF>" in input:
            # I'm guessing this should be a NAF file but something is wrong
            logging.exception("Error parsing NAF file")
            raise
        naf = KafNafParser(type="NAF")
        naf.set_version("3.0")
        naf.set_language("nl")
        naf.lang = "nl"
        naf.raw = input
        naf.set_raw(naf.raw)
    return naf


# TODO add functionality
def parse(input_file, max_min_per_sent=None):
    if isinstance(input_file, KafNafParser):
        in_obj = input_file
    else:
        in_obj = get_naf(input_file)

    lang = in_obj.get_language()
    if lang != 'nl':
        logging.warning('ERROR! Language is {} and must be nl (Dutch)'
                        .format(lang))
        sys.exit(-1)

    return in_obj
