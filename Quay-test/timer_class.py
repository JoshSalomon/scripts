
import datetime

class TimerAPI(object):
    def __init__(self):
        self.start_time = None
        self.stats = []

    def start(self):
        self.start_time = datetime.datetime.now()

    def diff_in_millis(self):
        assert self.start_time is not None
        diff = datetime.datetime.now() - self.start_time
        diff_millis = diff.microseconds / 1000  # convert microseconds to milliseconds
        diff_millis += diff.seconds * 1000      # convert seconds to milliseconds
        diff_millis += diff.days * 24 * 3600 * 1000 # convert days to milliseconds
        return int(diff_millis)

    def add_stat(self, millis, measure):
        self.stats.append((millis, measure))

    def print_stats(self):
        for s in self.stats:
            print(f'time: {s[0]} - value:{s[1]}')
