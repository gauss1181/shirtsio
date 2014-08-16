import json
import logging
import time

import requests

from django.conf import settings
from django.utils.http import urlquote

from pprint import pprint

logger = logging.getLogger(__name__)

class ShirtsioException(Exception):
    """Wrap specific API errors"""
    pass

class ShirtsioAPI(object):
    """Basic Python wrapper for Shirts.io API"""

    def __init__(self, debug=False):
        self.debug = debug
