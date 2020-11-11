# -*- coding: utf-8 -*-
from . import __version__
import logging

import stanza
from KafNafParserPy import *
from lxml.etree import XMLSyntaxError
from io import BytesIO
import sys
from itertools import groupby
from operator import itemgetter
from xml.sax.saxutils import escape

logger = logging.getLogger(__name__)
this_name = 'Morphosyntactic parser based on stanza'
default_treebank = 'alpino'


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
    offsets = {}
    txt = knaf_obj.get_raw()
    for sid, sentence in enumerate(st_doc.sentences):
        id_to_tokenid[sid+1] = {}
        for token in sentence.tokens:
            token_obj = Cwf(type=knaf_obj.get_type())
            token_id = 'w{}'.format(wcount)
            token_length = len(token.text)
            offsets[wcount] = txt.find(token.text, offsets.get(wcount-1, 0))
            token_obj.set_id(token_id)
            token_obj.set_length(str(token_length))
            # token_obj.set_offset(str(offset)) # Is this correct????
            token_obj.set_para('1')
            token_obj.set_sent(str(sid+1))
            token_obj.set_text(token.text)
            token_obj.set_offset(str(offsets[wcount]))

            wcount += 1
            id_to_tokenid[sid+1][token.id[0]] = token_id
            knaf_obj.add_wf(token_obj)
    return id_to_tokenid


def get_term_type(pos):
    if pos in ['det', 'pron', 'prep', 'vg', 'conj']:
        return 'close'
    else:
        return 'open'


def create_term_layer(st_doc, knaf_obj, id_to_tokenid):
    tcount = 0
    term_id_mapping = {}  # Mapping from stanford word index -> NAF term id
    for sid, sentence in enumerate(st_doc.sentences):
        for term in sentence.words:
            new_term_id = 't_'+str(tcount)
            term_id_mapping[(sid, term.id)] = new_term_id
            term_obj = Cterm(type=knaf_obj.get_type())
            term_obj.set_id(new_term_id)

            new_span = Cspan()
            new_span.create_from_ids([id_to_tokenid[sid+1]
                                      [term.parent.id[0]]])
            term_obj.set_span(new_span)

            # lemma: copy from stanza
            term_obj.set_lemma(term.lemma)

            # pos: take the UD UPOS value
            term_obj.set_pos(term.upos.lower())

            # external reference: the UD FEATS value
            if term.feats:
                ext_ref = CexternalReference()
                ext_ref.set_resource('Stanza')
                ext_ref.set_reftype('FEATS')
                ext_ref.set_reference(term.feats)
                term_obj.add_external_reference(ext_ref)

            # morphofeat: reformatted UD XPOS value
            if term.xpos:
                feats = term.xpos.split('|')
                feat = feats[0] + '(' + ','.join(feats[1:]) + ')'
                term_obj.set_morphofeat(feat)

            termtype = get_term_type(term.upos.lower())
            term_obj.set_type(termtype)

            knaf_obj.add_term(term_obj)

            tcount += 1
    return term_id_mapping


def create_dependency_layer(st_doc, knaf_obj, term_id_mapping):
    for s_id, sent in enumerate(st_doc.sentences):
        for source, rel, target in sent.dependencies:
            # Do not include root
            if rel != 'root':
                # Creating comment
                str_comment = ' '+rel+'('+str(target.lemma)+','+str(source.lemma)+') '
                str_comment = escape(str_comment, {"--": "&ndash"})

                my_dep = Cdependency()
                my_dep.set_from(term_id_mapping.get((s_id, source.id)))
                my_dep.set_to(term_id_mapping.get((s_id, target.id)))
                my_dep.set_function(rel)
                my_dep.set_comment(str_comment)
                knaf_obj.add_dependency(my_dep)


def add_linguistic_processors(in_obj, added_text_layer, treebank):
    name = this_name + ' using {} treebank'.format(treebank)

    if added_text_layer:
        my_lp = Clp()
        my_lp.set_name(name)
        my_lp.set_version(__version__)
        my_lp.set_timestamp()
        in_obj.add_linguistic_processor('text', my_lp)

    my_lp = Clp()
    my_lp.set_name(name)
    my_lp.set_version(__version__)
    my_lp.set_timestamp()
    in_obj.add_linguistic_processor('terms', my_lp)

    my_lp = Clp()
    my_lp.set_name(name)
    my_lp.set_version(__version__)
    my_lp.set_timestamp()
    in_obj.add_linguistic_processor('deps', my_lp)

    return in_obj


def parse(input_file, treebank=None):
    treebank = treebank if treebank is not None else default_treebank

    if isinstance(input_file, KafNafParser):
        in_obj = input_file
    else:
        in_obj = get_naf(input_file)

    lang = in_obj.get_language()
    if lang != 'nl':
        logging.warning('ERROR! Language is {} and must be nl (Dutch)'
                        .format(lang))
        sys.exit(-1)

    if in_obj.text_layer is None:
        added_text_layer = True
        nlp = stanza.Pipeline(lang='nl',
                              processors='tokenize,pos,lemma,depparse',
                              package=treebank)
        text = in_obj.get_raw()
        in_obj.remove_text_layer()
        doc = nlp(text)
        id_to_tokenid = create_text_layer(doc, in_obj)
    else:
        # Use existing tokenization
        added_text_layer = False
        nlp = stanza.Pipeline(lang='nl',
                                   tokenize_pretokenized=True,
                                   processors='tokenize,pos,lemma,depparse',
                                   package=treebank)
        sent_tokens_ixa = [(token.get_sent(), token.get_text())
                           for token in in_obj.get_tokens()]
        text = [[t for s2, t in toks]
                for s, toks in groupby(sent_tokens_ixa, itemgetter(0))]
        # TODO: is this correct??? can we make it more elegant?
        id_to_tokenid = {int(k):
                         {i+1: t.get_id() for i, t in enumerate(g)}
                         for k, g in
                         groupby(in_obj.get_tokens(), lambda t: t.get_sent())}
        doc = nlp(text)
        # Check that we don't get mutli-word get_tokens
        if any([len(sent.tokens) != len(sent.words)
                for sent in doc.sentences]):
            raise Exception('stanza returns MutliWordTokens. '
                            'This is not allowed for Dutch.')

    term_id_mapping = create_term_layer(doc, in_obj, id_to_tokenid)
    create_dependency_layer(doc, in_obj, term_id_mapping)

    in_obj = add_linguistic_processors(in_obj, added_text_layer, treebank)
    return in_obj
