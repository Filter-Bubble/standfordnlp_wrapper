import os
import io

from stanfordnlp_wrapper import parse

__here__ = os.path.dirname(os.path.realpath(__file__))
txt = b'''Dit is een tekst. Er zijn twee zinnen.'''


def assert_equal(val1, val2):
    assert val1 == val2


def test_tokenize():
    my_obj = parse(io.BytesIO(txt))
    token_list = list(my_obj.get_tokens())
    assert_equal(len(token_list), 10)
    last_token = token_list[-1]
    assert_equal(last_token.get_offset(), str(len(txt)-1))

    # Check linguistic processor layers
    layers = list(my_obj.get_linguisticProcessors())
    assert_equal(len(layers), 3)
