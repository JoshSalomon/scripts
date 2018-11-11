import json
import quay_constants as const

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
            print(url)
        r = self.session.get(url, **kwargs)
        if const.DEBUG.print_status_code:
            print("Status code = %d" % r.status_code)
        if const.DEBUG.print_response:
            print(r)
        if const.DEBUG.print_headers:
            print(r.headers)
        return r
