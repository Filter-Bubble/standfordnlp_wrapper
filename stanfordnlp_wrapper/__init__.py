# -*- coding: utf-8 -*-

import logging

from .__version__ import __version__
from .stanfordnlp_wrapper import parse

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Dafne van Kuppevelt"
__email__ = 'd.vankuppevelt@esciencecenter.nl'
