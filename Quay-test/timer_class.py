
import datetime
import logging
from pusher import MB_IN_BYTES, KB_IN_BYTES


class TimerAPI(object):
    def __init__(self):
        self.start_time = None
        self.stats = []
        self.bandwidth_kbs = 0
        self.total_capacity = 0

    def start(self):
        self.start_time = datetime.datetime.now()

    def diff_in_millis(self):
        assert self.start_time is not None
        diff = datetime.datetime.now() - self.start_time
        diff_millis = diff.microseconds / 1000          # convert microseconds to milliseconds
        diff_millis += diff.seconds * 1000              # convert seconds to milliseconds
        diff_millis += diff.days * 24 * 3600 * 1000     # convert days to milliseconds
        return int(diff_millis)

    def diff_in_seconds(self):
        diff = datetime.datetime.now() - self.start_time
        diff_secs = diff.seconds
        if diff.days > 0:
            diff_secs += (diff.days * 24 * 3600)
        return int(diff_secs)

    def add_stat(self, millis, measure):
        self.stats.append((millis, measure))

    def print_stats(self):
        for s in self.stats:
            logging.debug('time: %d - value: %d' % (int(s[0]), int(s[1])))
        aggr_time = 0
        aggr_capacity = 0
        for s in self.stats:
            aggr_time += int(s[0])
            aggr_capacity += int(s[1])
        self.total_capacity = aggr_capacity
        if aggr_time != 0:
            self.bandwidth_kbs = (aggr_capacity / 1024) / (aggr_time / 1000)
            if self.total_capacity < (100 * MB_IN_BYTES):
                cap = int(self.total_capacity / KB_IN_BYTES)
                cap_unit = "KB"
            else:
                cap = int(self.total_capacity / MB_IN_BYTES)
                cap_unit = "MB"
            logging.info('Average bandwidth for large requests = {:,} KB/s - total capacity = {:,} {}'.format
                         (int(self.bandwidth_kbs), cap, cap_unit))

    def bandwidth(self):
        return self.bandwidth_kbs, self.total_capacity

    @property
    def capacity(self):
        cap = 0
        for s in self.stats:
            cap += int(s[1])
        return cap

