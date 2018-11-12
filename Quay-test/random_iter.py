#
# Random iterator over a list.
# The method - create a list in the size of the original size (by calling init(size) method). Every iteration
# (call the next() method), a random number is selected and the item from the list is removed. The index is returned
# and the list becomes shorter by one.
#
import random


class RandomIter(object):
    def __init__(self):
        self.iter_list = []
        pass

    def init(self, size):
        self.iter_list = [i for i in range(size)]

    def next(self):
        if len(self.iter_list) <= 0:
            return None
        print("iter next, len=%d, iter_list=%s" % (len(self.iter_list), self.iter_list), end="")
        index = random.randint(0, len(self.iter_list) - 1)
        print(" index=%d, value=%d" % (index, self.iter_list[index]), end="")
        rc = self.iter_list.pop(index)
        print(" after pop list=%s" % self.iter_list)
        return rc
