#  QUAY_DOMAIN = 'quay.io'
#  QUAY_URL = 'https://' + QUAY_DOMAIN
QUAY_DOMAIN = 'andromeda03.sales.lab.tlv.redhat.com'
QUAY_URL = 'http://' + QUAY_DOMAIN + '/'
IMAGE_ID_LAST = '3690474eb5b4b26fdfbd89c6e159e8cc376ca76ef48032a30fa6aafd56337880'
IMAGE_ID_TOP = '03cffc43c0a5cf4268bbf830cf917e5d089f74e03609d1b3c79522e6043d769e'
NAMESPACE = 'biocontainers'
REPOSITORY = 'coreutils'

#
# If keeping this True - look in the code for some file locations in the code that relate
# to my local home directory (/home/jsalomon)
#
DEBUG = True        # emit some additional debug info and save some additional files
#
# List of Quay V1 APIs
#
QUAY_API_URL = QUAY_URL + 'api/v1/'
QUAY_API_TOKEN = 'tBmnKXZ39wlwMchGR6DOqv4LjNBJkazFqsH3uHEz'
#
Q_API_REPOSITORY = 'repository'

#
# List of docker V2 APIs (as described in docker documentation) - These APIs
# are implemented by Quay, but quay does not control its definifion.
#
DOCKER_API_URL = QUAY_URL + 'v2/'
#
D_API_AUTH = 'auth'
D_API_CATALOG = '_catalog'

TEST_USERNAME = 'test_runner'
TEST_PWD = 'redhat12'
TEST_TAG = 'use_in_test'

REP_NAME1 = 'test_runner/test1'
IMG_DIGEST1 = 'sha256:7771a5939ec5f4ce72f9659be8c212b5862139de58c4e68e67b30601063048d8'
