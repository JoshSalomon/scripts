#
# global imports
#
import threading
import logging
import os
import random
import time
import hashlib
from base_thread import LoadTestThread
import json
from Cryptodome.PublicKey import RSA
from jwkest.jwk import RSAKey

#
# local imports
#
import config
import quay_utils
import docker_v2_apis
import docker_image

KB_IN_BYTES = 1024
MB_IN_BYTES = 1024 * KB_IN_BYTES
GB_IN_BYTES = 1024 * MB_IN_BYTES

DEF_MINSIZE = 100 * KB_IN_BYTES
# DEF_MAXSIZE = 2 * GB_IN_BYTES
DEF_MAXSIZE = 80 * MB_IN_BYTES  # For debug use smaller sizes.
CHUNK_SIZE = 2 * MB_IN_BYTES

c = config.Config()


class Pusher(LoadTestThread):
    def __init__(self, name, credentials, repo_name, tag_prefix='Tag'):
        super().__init__(name, credentials)
        self.__repo_name__ = repo_name
        self.__tag_prefix__ = tag_prefix
        self.__stop_event__ = threading.Event()
#        self.jwk = RSAKey(key=RSA.generate(2048).publickey()).serialize(True)
        self.jwk = RSAKey(key=RSA.generate(2048)).serialize(True)
        #self.jwk.get()

    def run(self, wait_multiply=0):
        # todo - login and keep token in
        self.push()
        return
        time_in_secs = 1
        while not self.__stop_event__.is_set():
            # time_in_secs = push....
            self.__stop_event__.wait(wait_multiply * time_in_secs)
        return

    def push(self, n_images=1, min_size=DEF_MINSIZE, max_size=DEF_MAXSIZE):
        options = ProtocolOptions()
        tag_rand = random.randint(1024, 1024*1024*16)
        tag_name = '%s%06x' % (self.__tag_prefix__,  tag_rand)
        header = {
            'Accept': options.accept_mimetypes,
        }
        # ping?
        # assumption - we already logged in and the credentials are already set
        # currently ignoring n_images!
        dckr_image = self.build_single_image_manifest(tag_name, min_size, max_size)
        self.d_api.push_single_image(self.__repo_name__, dckr_image, header)

    def build_single_image_manifest(self, tag_name, min_size, max_size):
        image = quay_utils.create_random_image(min_size, max_size, tag_name[len(self.__tag_prefix__):])
        checksum = 'sha256:' + hashlib.sha256(image['contents']).hexdigest()
#        layer_dict = {'id': image['id'], 'parent': '', 'Size': image['Size']}
        layer_dict = {'id': image['id'], 'Size': image['Size']}
        builder = quay_utils.DockerSchema1ManifestBuilder('', self.__repo_name__, tag_name)
        builder.add_layer(checksum, json.dumps(layer_dict))
        manifest = builder.build(self.jwk)
        # checksums = {image.id: checksum}
        dckr_image = docker_image.DockerImage(manifest, checksum, image['contents'], layer_dict, tag_name)
        return dckr_image


class ProtocolOptions(object):
    def __init__(self):
        self.munge_shas = False
        self.scopes = None
        self.cancel_blob_upload = False
        self.manifest_invalid_blob_references = False
        self.chunks_for_upload = None
        self.skip_head_checks = False
        self.manifest_content_type = None
        self.accept_mimetypes = '*/*'
        self.mount_blobs = None
        self.push_by_manifest_digest = False
