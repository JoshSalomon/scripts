
import datetime
import logging


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
            logging.info('Average bandwidth for large requests = %d KB/s - total capacity = %d' %
                         (int(self.bandwidth_kbs), self.total_capacity))

    def bandwidth(self):
        return self.bandwidth_kbs, self.total_capacity
