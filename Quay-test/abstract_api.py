import json
import quay_constants as const
import logging
import requests

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
            logging.debug('GET: %s' % url)
        try:
            r = self.session.get(url, **kwargs)
            if const.DEBUG.print_status_code:
                logging.debug("Status code = %d" % r.status_code)
            success = r.status_code / 100 == 2
            if const.DEBUG.print_response or not success:
                logging.debug(r)
            if const.DEBUG.print_headers or not success:
                logging.debug(r.headers)
            if not success:
                if r.headers['Content-Type'] == 'application/json':
                    json_response = self.json_decoder.decode(r.text)
                    logging.info(json_response)
        except requests.exceptions.Timeout as et:
            logging.error("Connection timeout")
            logging.error(" == Cause: <%s>" % et.__cause__)
            logging.error(" == Context <%s>" % et.__context__)
        except requests.exceptions.TooManyRedirects as etmr:
            logging.error("Too many redirects")
            logging.error(" == Cause: <%s>" % etmr.__cause__)
            logging.error(" == Context <%s>" % etmr.__context__)
        except requests.exceptions.ConnectionError as ece:
            logging.error("Connection Error")
            logging.error(" == Cause: <%s>" % ece.__cause__)
            logging.error(" == Context <%s>" % ece.__context__)
        except requests.exceptions.HTTPError as ehttp:
            logging.error("HTTP Error")
            logging.error(" == Cause: <%s>" % ehttp.__cause__)
            logging.error(" == Context <%s>" % ehttp.__context__)
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r

    def head(self, url, **kwargs):
        self.set_token()
        if const.DEBUG.print_request:
            logging.debug('HEAD: %s' % url)
        r = self.session.head(url, **kwargs)
        if const.DEBUG.print_status_code:
            logging.debug("Status code = %d" % r.status_code)
        if const.DEBUG.print_response:
            logging.debug(r)
        if const.DEBUG.print_headers:
            logging.debug(r.headers)
        return r
