from KafNafParserPy import KafNafParser
import os
import sys
import subprocess
from io import BytesIO

from stanfordnlp_wrapper import parse

__here__ = os.path.dirname(os.path.realpath(__file__))


def assert_equal(val1, val2):
    assert val1 == val2


def _test_file1(this_file):
    my_obj = parse(open(this_file, 'rb'))

    # Check the terms
    terms = [term for term in my_obj.get_terms()]
    assert_equal(len(terms), 12)
    assert_equal(terms[4].get_lemma(), 'mooi')
    assert_equal(terms[4].get_pos(), 'adj')

    # Check dependencies
    dependencies = [dep for dep in my_obj.get_dependencies()]
    assert_equal(len(dependencies), 10)

    # TODO: check dependencies in more detail

def _test_file2(this_file):
    my_obj = parse(open(this_file, 'rb'))
    # Check the terms
    terms = [term for term in my_obj.get_terms()]
    assert_equal(len(terms), 61)



def test_morphosyn_kaf():
    kaf_file = os.path.join(__here__, 'test_files', 'file1.in.kaf')
    _test_file1(kaf_file)


def test_morphosyn_naf():
    naf_file = os.path.join(__here__, 'test_files', 'file1.in.naf')
    _test_file1(naf_file)

def test_stanfordnlp():
    naf_file = os.path.join(__here__, 'test_files', 'file3.in.naf')
