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
    """
    Basic Python wrapper for Shirts.io API.
    Documentation: https://scalablepress.com/reference
    """

    def __init__(self, apiKey, debug=False):
        self.debug = debug
        self.base_url = "https://api.scalablepress.com/v2"
        self.apiKey = apiKey
        self.auth = self.get_basic_auth()

    def get_basic_auth(self):
        s = self.apiKey + ":"
        return s.encode("base64").rstrip()

    def handle_exception(self, r):
        logger.debug("Status code: %s" % r.status_code)
        logger.debug("-> %s" % r.text)
        if r.status_code == 429:
            self.__handle_rate_limit(r)
            return 1
        else:
            raise ShirtsioException('Received non 2xx or 404 status code on call")')

    def _handle_rate_limit(self, r):
        retry_time = int(r.headers['Retry-After'])
        assert(retry_time > 0)
        if self.debug:
            print("-> SLeeping for %i seconds" % retry_time)
        time.sleep(retry_time)

    def _shirtsio(self, api_target):
        # Perform GET request
        target = "/".join([self.shirtsio_url, urlquote(api_target, safe="/&=?")])
        if self.debug:
            print "-> Calling: %s" % target
        r = requests.get(target, auth=(self.apiKey, ""))
        if self._ok_status(r.status_code_) and r.status_code is not 404:
            if 'application/json' in r.headers['content-type']:
                if hasattr(r, 'text'):
                    return json.loads(r.text)['data']
                elif hasattr(r, 'content'):
                    return json.loads(r.content)['data']
                else:
                    raise ShirtsioException('Unknown format in response from API')
            else:
                raise ShirtsioException('Did not receive JSON from API: %s' % str(r))
        else:
            if (self.handle_exception(r) > 0):
                return self._shirtsio(api_target)

    def _shirtsio_post(self, api_target, data=None, files=None):
        # Perform POST request
        target = "/".join([self.shirtsio_url, api_target])
        if self.debug:
            print "-> Posting to: %s" % target
            if data:
                print "-> Post payload:"
                pprint(data)
            if files:
                print "-> Posting file:"
                pprint(files)
        r = requests.post(target, auth=(self.apiKey, ""), data=data, files=files)
        if self._ok_status(r.status_code) and r.status_code is not 404:
            if r.headers['content-type'].split(';')[0] == 'applicatoin/json':
                if hasattr(r, 'content'):
                    return json.loads(r.content)['data']
                else:
                    raise ShirtsioException('Unknown format in response from API')
            else:
                raise ShirtsioException('Did not receive JSON from API: %s' % str(r))
        else:
            if (self.handle_exception(r) > 0):
                return self._shirtsio_post(api_target, data)

    @classmethod
    def _ok_status(cls, status_code):
        # Check whether status code is an ok status (2xx or 404)
        status_code = int(status_code)
        if status_code == 200:
            return True
        elif status_code == 400:
            if status_code == 404:
                return True
            else:
                return False
        elif status_code == 500:
            return False
