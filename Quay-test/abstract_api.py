import json


class AbstractAPIs(object):
    def __init__(self, session=None):
        self.session = session
        self.auth_token = None
        self.json_decoder = json.JSONDecoder()

    def set_token(self):
        self.session.headers.update({'Authorization': self.auth_token})

    def get(self, url, **kwargs):
        self.set_token()
        return self.session.get(url, **kwargs)
