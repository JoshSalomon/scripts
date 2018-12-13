import json
import quay_constants as const
import logging
import requests
import time
import config
import sys

c = config.Config()

def debug_counter():
    return 1
    # if 'cnt' not in debug_counter.__dict__:
    #     debug_counter.cnt = 0
    # debug_counter.cnt += 1
    # return debug_counter.cnt


class AbstractAPIs(object):
    def __init__(self, session=None):
        self.session = session
        self.auth_token = None
        self.json_decoder = json.JSONDecoder()

    def set_token(self):
        self.session.headers.update({'Authorization': self.auth_token})

    def check_token_expiry(self, r):
        if r.status_code == 401:
            js = self.json_decoder.decode(r.text)
            if js['error'] is not None:
                msg = js['error']
            else:
                msg = ""
            logging.info(f"Authentication error on request {r.request.method} {r.request.url}")
            logging.info(f" -> retrying msg='{msg}'")
            if c.verbose_on_error:
                logging.getLogger().setLevel(logging.DEBUG)
            time.sleep(1)
            raise const.AppRetryException(msg=msg)
        if r.status_code == 500:
            # internal server error
            logging.info("Internal server error - waiting one second and retrying")
            time.sleep(1)
            raise const.AppRetryException(rc=500, msg="Internal server error", relogin=False)
        if debug_counter() % 45 == 0:
            raise const.AppRetryException()
        return

    def get(self, url, **kwargs):
        self.set_token()
        r = None
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
            self.check_token_expiry(r)
            if not success:
                if r.headers['Content-Type'] == 'application/json':
                    json_response = self.json_decoder.decode(r.text)
                    logging.info(json_response)
        except requests.exceptions.Timeout as et:
            logging.error("Connection timeout - retrying")
            logging.error(" == Cause: <%s>" % et.__cause__)
            logging.error(" == Context <%s>" % et.__context__)
            raise const.AppRetryException(-1, et.__context__, relogin=False)
        except requests.exceptions.TooManyRedirects as etmr:
            logging.error("Too many redirects")
            logging.error(" == Cause: <%s>" % etmr.__cause__)
            logging.error(" == Context <%s>" % etmr.__context__)
        except requests.exceptions.ConnectionError as ece:
            logging.error("Connection Error - retrying")
            logging.error(" == Cause: <%s>" % ece.__cause__)
            logging.error(" == Context <%s>" % ece.__context__)
            raise const.AppRetryException(-1, ece.__context__, relogin=False)
        except requests.exceptions.HTTPError as ehttp:
            logging.error("HTTP Error")
            logging.error(" == Cause: <%s>" % ehttp.__cause__)
            logging.error(" == Context <%s>" % ehttp.__context__)
        except const.AppRetryException as te:
            raise te
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r

    def head(self, url, **kwargs):
        self.set_token()
        r = None
        if const.DEBUG.print_request:
            logging.debug('HEAD: %s' % url)
        try:
            r = self.session.head(url, **kwargs)
            failure = r.status_code / 100 != 2
            if failure or const.DEBUG.print_status_code:
                logging.debug("Status code = %d" % r.status_code)
            if failure or const.DEBUG.print_response:
                logging.debug(r)
            if failure or const.DEBUG.print_headers:
                logging.debug(r.headers)
            self.check_token_expiry(r)
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
        except const.AppRetryException as te:
            raise te
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r

    def post(self, url, **kwargs):
        self.set_token()
        r = None
        logging.debug(self.session.headers)
        if const.DEBUG.print_request:
            logging.debug('POST: %s' % url)
        try:
            r = self.session.post(url, **kwargs)
            failure = r.status_code / 100 != 2
            if failure or const.DEBUG.print_status_code:
                logging.debug("Status code = %d" % r.status_code)
            if failure or const.DEBUG.print_response:
                logging.debug(r)
            if failure or const.DEBUG.print_headers:
                logging.debug(r.headers)
            self.check_token_expiry(r)
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
        except const.AppRetryException as te:
            raise te
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r

    def patch(self, url, **kwargs):
        self.set_token()
        r = None
        timeout = kwargs.pop('timeout', 2)
        logging.debug(f"*** Fixing timeout = {timeout}")
        if const.DEBUG.print_request:
            logging.debug('PATCH: %s' % url)
        try:
            r = self.session.patch(url, **kwargs, timeout=None)
            failure = r.status_code / 100 != 2
            if failure or const.DEBUG.print_status_code:
                logging.debug("Status code = %d" % r.status_code)
            if failure or const.DEBUG.print_response:
                logging.debug(r)
            if failure or const.DEBUG.print_headers:
                logging.debug(r.headers)
            self.check_token_expiry(r)
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
        except const.AppRetryException as te:
            raise te
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r

    def put(self, url, **kwargs):
        self.set_token()
        r = None
        if const.DEBUG.print_request:
            logging.debug('PUT: %s' % url)
        try:
            r = self.session.put(url, **kwargs)
            failure = r.status_code / 100 != 2
            if failure or const.DEBUG.print_status_code:
                logging.debug("Status code = %d" % r.status_code)
            if failure or const.DEBUG.print_response:
                logging.debug(r)
            if failure or const.DEBUG.print_headers:
                logging.debug(r.headers)
            self.check_token_expiry(r)
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
        except const.AppRetryException as te:
            raise te
        except Exception as e:
            logging.error("Unexpected error")
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
        return r
