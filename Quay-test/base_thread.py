
from threading import Thread


class LoadTestThread(Thread):
    def __init__(self, name, credentials):
        Thread.__init__(self)
        self.name = name
        self.ip_address = credentials[0]
        self.d_api = credentials[1]


