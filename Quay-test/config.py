from enum import Enum, auto

import quay_constants

DIFF_INFINITE = int(1024 * 1024 * 1024)


class Command(Enum):
    PUSH = auto()
    PULL = auto()


# todo - add max tags to read. just to make some runs faster.
#
# This class is a singleton, this is implemented in the __new__ method
#
class Config(object):
    __instance = None

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = object.__new__(cls)
        return Config.__instance

    def __init__(self):
        self.__threads = quay_constants.DEF_NUM_THREADS
        self.__cycles = quay_constants.DEF_CYCLES
        self.__quay_ips = quay_constants.QUAY_DOMAINS
        self.__quay_port = quay_constants.QUAY_PORT
        self.__use_https = quay_constants.DEF_USE_HTTPS
        self.__verbose = quay_constants.DEF_VERBOSE
        self.__username = quay_constants.TEST_USERNAME
        self.__password = quay_constants.TEST_PWD
        self.__default_password = True
        self.__push_size_gb = quay_constants.DEF_RUN_PUSH_SIZE_GB
        self.__num_upload_images = quay_constants.DEF_UPLOAD_IMAGES
        self.__millis_to_end = DIFF_INFINITE
        self.__wait_between_ops = 0
        self.__verbose_on_error = False
        self.__max_tags = 0
        self.__dont_run = False

    @property
    def threads(self):
        return self.__threads

    @threads.setter
    def threads(self, threads):
        self.__threads = threads

    @property
    def cycles(self):
        return self.__cycles

    @cycles.setter
    def cycles(self, cycles):
        self.__cycles = cycles

    @property
    def verbose(self):
        return self.__verbose

    @verbose.setter
    def verbose(self, verbose):
        self.__verbose = verbose

    @property
    def max_tags(self):
        return self.__max_tags

    @max_tags.setter
    def max_tags(self, max_tags):
        self.__max_tags = max_tags

    @property
    def quay_ips(self):
        return self.__quay_ips

    @quay_ips.setter
    def quay_ips(self, ip):
        if isinstance(ip, list):
            self.__quay_ips = ip
        else:
            self.__quay_ips = [ip]

    def quay_ips_as_str(self):
        rc = ""
        if len(self.quay_ips) > 1:
            for i in range(len(self.quay_ips) - 1):
                rc += self.quay_ips[i]
                rc += ","
        if self.quay_ips:       # empty list returns False
            rc += self.quay_ips[-1]
        return rc

    @property
    def quay_port(self):
        return self.__quay_port

    @quay_port.setter
    def quay_port(self, port):
        self.__quay_port = port

    @property
    def use_https(self):
        return self.__use_https

    @use_https.setter
    def use_https(self, enable):
        self.__use_https = enable

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password
        self.__default_password = False

    @property
    def push_size_gb(self):
        return self.__push_size_gb

    @push_size_gb.setter
    def push_size_gb(self, size_gb):
        self.__push_size_gb = int(size_gb)

    def docker_api_url(self, ip_address):
        rc = ""
        if self.__use_https:
            rc += "https://"
        else:
            rc += "http://"
        if ip_address is not None:
            rc += ip_address
        else:
            rc += self.__quay_ips[0]
        if self.__quay_port is not None:
            rc += (":%d" % self.__quay_port)
        rc += "/v2/"
        return rc

    @property
    def millis_to_end(self):
        return self.__millis_to_end

    @millis_to_end.setter
    def millis_to_end(self, millis):
        self.__millis_to_end = millis

    @property
    def seconds_to_end(self):
        return self.__millis_to_end / 1000

    @seconds_to_end.setter
    def seconds_to_end(self, seconds):
        self.__millis_to_end = int(seconds) * 1000
        print(self.millis_to_end)

    @property
    def num_upload_images(self):
        return self.__num_upload_images

    @num_upload_images.setter
    def num_upload_images(self, num_upload_images):
        self.__num_upload_images = int(num_upload_images)

    def docker_api_domain(self, ip_address):
        if ip_address is not None:
            rc = ip_address
        else:
            rc = self.__quay_ips[0]
        if self.__quay_port is not None:
            rc += (":%d" % self.__quay_port)
        return rc

    @property
    def verbose_on_error(self):
        return self.__verbose_on_error

    @verbose_on_error.setter
    def verbose_on_error(self, verbose):
        self.__verbose_on_error = verbose

    @property
    def wait_between_ops(self):
        return self.__wait_between_ops

    @wait_between_ops.setter
    def wait_between_ops(self, wait_in_secs):
        self.__wait_between_ops = wait_in_secs

    @property
    def dont_run(self):
        return self.__dont_run

    @dont_run.setter
    def dont_run(self, dont_run):
        self.__dont_run = dont_run

    def print(self, command):
        print("Current test configuration:")
        print(f" => Quay server address: {self.quay_ips_as_str()}")
        print(f" => Quay server port: {self.__quay_port}")
        protocol = "https" if self.use_https else "http"
        print(f" => Communication protocol: {protocol}")
        print(f" => Quay username: {self.username}")
        password = "*default*" if self.__default_password else self.password
        print(f" => Password: {password}")
        print(f" => Number of threads: {self.threads}")
        if command == Command.PULL:
            print(f" => Number of repository iterations per thread: {self.cycles}")
            if self.millis_to_end == DIFF_INFINITE:
                print(" => Test will iterate over the entire repository")
            else:
                print(f" => Test will complete after {int(self.millis_to_end / 1000)} seconds")
            if self.dont_run <= 0:
                print(" => Read all the tags in the repository before start pulling")
            else:
                print(f" => Read {self.max_tags} tags before start pulling images")
        if command == Command.PUSH:
            if self.push_size_gb > 0:
                print(f" => Push {self.push_size_gb} GBs of data into the repository")
            else:
                print(f" => Push {self.num_upload_images} images into the repository")
            if self.wait_between_ops <= 0:
                print(f" => No wait between push requests")
            else:
                print(f" => Test waits {self.wait_between_ops} seconds between push requests")
        verbose_mode = "On" if self.verbose else "Off"
        print(f" => Verbose: {verbose_mode}")
        verbose_on_error_mode = "On" if self.verbose_on_error else "Off"
        print(f" => Verbose on error: {verbose_on_error_mode}")
        print(f" => Don't run = {self.dont_run}")
