#
# Random iterator over a list.
# The method - create a list in the size of the original size (by calling init(size) method). Every iteration
# (call the next() method), a random number is selected and the item from the list is removed. The index is returned
# and the list becomes shorter by one.
#
import random
import quay_constants
import logging


class RandomIter(object):
    def __init__(self):
        self.iter_list = []
        pass

    def init(self, size):
        self.iter_list = [i for i in range(size)]

    def next(self):
        if len(self.iter_list) <= 0:
            return None
        if quay_constants.DEBUG.print_debug_info:
            msg_head = "iter next, len=%d, iter_list=%s" % (len(self.iter_list), self.iter_list)
        index = random.randint(0, len(self.iter_list) - 1)
        if quay_constants.DEBUG.print_debug_info:
            msg_head += " index=%d, value=%d" % (index, self.iter_list[index])
        rc = self.iter_list.pop(index)
        if quay_constants.DEBUG.print_debug_info:
            logging.debug("%s after pop list=%s" % (msg_head, self.iter_list))
        return rc
