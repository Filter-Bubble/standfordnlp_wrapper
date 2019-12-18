# -*- coding: utf-8 -*-
import logging

import stanfordnlp
import KafNafParserPy
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

def create_text_layer(st_doc, knaf_obj):
    id_to_tokenid = {}
    wcount = 1
    offset = 0
    for sid, sentence in enumerate(st_doc.sentences):
        id_to_tokenid[sid+1] = {}
        for token in sentence.tokens:
            token_obj = KafNafParserPy.Cwf(type=knaf_obj.get_type())
            token_id = 'w{}'.format(wcount)
            token_length = len(token.text)
            token_obj.set_id(token_id)
            token_obj.set_length(str(token_length))
            #token_obj.set_offset(str(offset)) # Is this correct????
            token_obj.set_para('1')
            token_obj.set_sent(str(sid+1))
            token_obj.set_text(token.text)
            wcount += 1
            offset += token_length # TODO fix
            id_to_tokenid[sid+1][token.index] = token_id
            knaf_obj.add_wf(token_obj)
    return id_to_tokenid


def get_term_type(pos):
    if pos in ['det','pron','prep','vg','conj' ]:
        return 'close'
    else:
        return 'open'

def create_term_layer(st_doc, knaf_obj, id_to_tokenid):
    tcount = 0
    for sid, sentence in enumerate(st_doc.sentences):
        for term in sentence.words:
            new_term_id = 't_'+str(tcount)

            term_obj = KafNafParserPy.Cterm(type=knaf_obj.get_type())
            term_obj.set_id(new_term_id)

            new_span = KafNafParserPy.Cspan()
            new_span.create_from_ids([id_to_tokenid[sid+1][term.parent_token.index]])
            term_obj.set_span(new_span)

            term_obj.set_lemma(term.lemma)

            # TODO map pos tags to universal tag?
            pos = term.upos.lower()
            term_obj.set_pos(pos)

            feats = term.pos.split('|') #term.feats)
            feats = feats[0]+'(' + ','.join(feats[1:]) + ')'
            term_obj.set_morphofeat(feats)

            termtype = get_term_type(pos)
            term_obj.set_type(termtype)
            knaf_obj.add_term(term_obj)

            tcount += 1

def recover_raw_text(knaf_obj):
    text = ''
    for t in knaf_obj.get_tokens():
        offset = t.get_offset()
        if offset is None:
            offset = len(text) + 1
        else:
            offset = int(offset)
        if  offset > len(text):
            text = text + ' '*(offset - len(text))
        text = text + t.get_text()

    return text

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

    nlp = stanfordnlp.Pipeline(lang='nl')
    text = in_obj.get_raw()
    if text is None:
        # TODO: throw warning? and add raw layer?
        text = recover_raw_text(in_obj)
    doc = nlp(text)

    in_obj.remove_text_layer()
    id_to_tokenid = create_text_layer(doc, in_obj)
    create_term_layer(doc, in_obj, id_to_tokenid)

    return in_obj
