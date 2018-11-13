import json
import quay_constants as const
import logging

class AbstractAPIs(object):
    def __init__(self, session=None):
        self.session = session
        self.auth_token = None
        self.json_decoder = json.JSONDecoder()

    def set_token(self):
        self.session.headers.update({'Authorization': self.auth_token})

    def get(self, url, **kwargs):
        self.set_token()
        if const.DEBUG.print_request:
            logging.debug(url)
        r = self.session.get(url, **kwargs)
        if const.DEBUG.print_status_code:
            logging.debug("Status code = %d" % r.status_code)
        if const.DEBUG.print_response:
            logging.debug(r)
        if const.DEBUG.print_headers:
            logging.debug(r.headers)
        return r
