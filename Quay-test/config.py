
import quay_constants


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
        self.__quay_ip = quay_constants.QUAY_DOMAIN
        self.__quay_port = None
        self.__use_https = quay_constants.DEF_USE_HTTPS
        self.__verbose = quay_constants.DEF_VERBOSE
        self.__username = quay_constants.TEST_USERNAME
        self.__password = quay_constants.TEST_PWD
        self.__default_password = True

    @property
    def threads(self):
        return self.__threads

    def set_threads(self, threads):
        self.__threads = threads

    @property
    def cycles(self):
        return self.__cycles

    def set_cycles(self, cycles):
        self.__cycles = cycles

    @property
    def verbose(self):
        return self.__verbose

    def set_verbose(self, verbose):
        self.__verbose = verbose

    @property
    def quay_ip(self):
        return self.__quay_ip

    def set_quay_ip(self, ip):
        self.__quay_ip = ip

    @property
    def quay_port(self):
        return self.__quay_port

    def set_quay_port(self, port):
        self.__quay_port = port

    @property
    def use_https(self):
        return self.__use_https

    def enable_https(self):
        self.__use_https = True

    @property
    def verbose(self):
        return self.__verbose

    def set_verbose(self, verbose):
        self.__verbose = verbose

    @property
    def username(self):
        return self.__username

    def set_username(self, username):
        self.__username = username

    @property
    def password(self):
        return self.__password

    def set_password(self, password):
        self.__password = password
        self.__default_password = False

    def docker_api_url(self):
        rc = ""
        if self.__use_https:
            rc += "https://"
        else:
            rc += "http://"
        rc += self.__quay_ip
        if self.__quay_port is not None:
            rc += (":%d" % self.__quay_port)
        rc += "/v2/"
        return rc

    def print(self):
        print("Current test configuration:")
        print(f" => Quay server address: {self.quay_ip}")
        print(f" => Quay server port: {self.__quay_port}")
        protocol = "https" if self.use_https else "http"
        print(f" => Communication protocol: {protocol}")
        print(f" => Quay username: {self.username}")
        password = "*default*" if self.__default_password else self.password
        print(f" => Password: {password}")
        print(f" => Number of threads: {self.threads}")
        print(f" => Number of repository iterations per thread: {self.cycles}")
        verbose_mode = "On" if self.verbose else "Off"
        print(f" => Verbose: {verbose_mode}")

