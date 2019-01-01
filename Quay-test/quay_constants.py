from enum import Flag, auto


class DebugLevel(Flag):
    NONE = 0
    REQUEST = auto()
    STATUS_CODE = auto()
    HEADERS = auto()
    RESPONSE = auto()
    DECODED_RESPONSE = auto()
    PROCESSED_RESPONSE = auto()
    SESSION = auto()
    DEBUG_INFO = auto()         # set manually for debug printing of the code, development cycle only
    ALL = REQUEST | STATUS_CODE | HEADERS | RESPONSE | DECODED_RESPONSE | PROCESSED_RESPONSE | SESSION


class Debug(object):
    debug_level = DebugLevel.REQUEST | DebugLevel.STATUS_CODE | DebugLevel.DECODED_RESPONSE | DebugLevel.HEADERS | \
                  DebugLevel.PROCESSED_RESPONSE
    # DebugLevel.RESPONSE | DebugLevel.PROCESSED_RESPONSE
    dl_stack = []

    @property
    def print_request(self):
        return self.debug_level & DebugLevel.REQUEST

    @property
    def print_response(self):
        return self.debug_level & DebugLevel.RESPONSE

    @property
    def print_status_code(self):
        return self.debug_level & DebugLevel.STATUS_CODE

    @property
    def print_headers(self):
        return self.debug_level & DebugLevel.HEADERS

    @property
    def print_decoded_response(self):
        return self.debug_level & DebugLevel.DECODED_RESPONSE

    @property
    def print_processed_response(self):
        return self.debug_level & DebugLevel.PROCESSED_RESPONSE

    @property
    def print_session(self):
        return self.debug_level & DebugLevel.SESSION

    @property
    def print_debug_info(self):
        return self.debug_level & DebugLevel.DEBUG_INFO

    def set_debug_level(self, new_level):
        self.debug_level = new_level

    @property
    def get_debug_level(self):
        return self.debug_level

    def push_debug_level(self, new_level):
        self.dl_stack.insert(0, self.get_debug_level)
        self.debug_level = new_level

    def pop_debug_level(self):
        if len(self.dl_stack) <= 0:
            raise Exception('Popping from empty debug level stack')
        else:
            self.debug_level = self.dl_stack.pop(0)

    def push_add_debug_info(self):
        self.push_debug_level(self.debug_level | DebugLevel.DEBUG_INFO)


class HttpAppException(Exception):
    def __init__(self, msg, status_code, orig_txt=""):
        """

        :rtype: object
        """
        self.__msg__ = msg
        self.__status_code__ = status_code
        self.__orig_txt__ = orig_txt
        pass


class AppRetryException(HttpAppException):
    def __init__(self, rc=401, msg="Token expired", relogin=True):
        super().__init__(msg, rc)
        self.__relogin = relogin

    @property
    def do_relogin(self):
        return self.__relogin


#
# If keeping this True - look in the code for some file locations in the code that relate
# to my local home directory (/home/jsalomon)
#
DEBUG = Debug()  # Control amount of output

#  QUAY_DOMAIN = 'quay.io'
#  QUAY_URL = 'https://' + QUAY_DOMAIN
# QUAY_DOMAINS = ['andromeda03.sales.lab.tlv.redhat.com']
# QUAY_DOMAINS = ['10.12.76.154', '10.12.76.167', '10.12.76.119']
# QUAY_DOMAINS = ['192.168.0.70', '192.168.0.80', '192.168.0.50']
# #QUAY_DOMAINS = ['10.12.70.153', '10.12.70.172', '10.12.70.187']  # CL_QUAY1
# #QUAY_DOMAINS = ['10.12.76.119']
QUAY_DOMAINS = ['10.12.76.139']  # HA_PROXY
IP_REPLACE_LIST = [('10.12.76.139', '192.168.0.60')]    # External and internal addresses of haproxy
QUAY_PORT = None
# ### QUAY_URL = 'http://' + QUAY_DOMAIN + '/'
# IMAGE_ID_LAST = '3690474eb5b4b26fdfbd89c6e159e8cc376ca76ef48032a30fa6aafd56337880'
# IMAGE_ID_TOP = '03cffc43c0a5cf4268bbf830cf917e5d089f74e03609d1b3c79522e6043d769e'
# NAMESPACE = 'biocontainers'
# REPOSITORY = 'coreutils'

#
# List of Quay V1 APIs
#
# ###QUAY_API_URL = QUAY_URL + 'api/v1/'
# ###QUAY_API_TOKEN = 'tBmnKXZ39wlwMchGR6DOqv4LjNBJkazFqsH3uHEz'
#
# ##Q_API_REPOSITORY = 'repository'

#
# List of docker V2 APIs (as described in docker documentation) - These APIs
# are implemented by Quay, but quay does not control its definifion.
#
# ###DOCKER_API_URL_OLD = QUAY_URL + 'v2/'

#
D_API_AUTH = 'auth'
D_API_CATALOG = '_catalog'

TEST_USERNAME = 'test_runner'
TEST_PWD = 'redhat12'

# ###REP_NAME1 = 'test_runner/test1'

####
# Default Values
####
DEF_NUM_THREADS = 3
DEF_CYCLES = 1
DEF_VERBOSE = False
DEF_USE_HTTPS = False
DEF_RUN_PUSH_SIZE_GB = 0
DEF_UPLOAD_IMAGES = 1
