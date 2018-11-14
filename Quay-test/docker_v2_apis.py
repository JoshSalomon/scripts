# import json
import os
#import datetime
# from requests import Session
import quay_constants as const
from abstract_api import AbstractAPIs
import gzip
from io import BytesIO, SEEK_END
import timer_class
import random_iter
import logging


class DockerV2Apis(AbstractAPIs):
    def __init__(self):
        super().__init__()

    def login(self, username, pwd, requests):
        params = {
            'account': username,
            'service': const.QUAY_DOMAIN,
            'scope': [],
        }
        if username is None:
            username = os.environ["QUAY_USERNAME"]
        if pwd is None:
            pwd = os.environ["QUAY_PWD"]

        auth = (username, pwd)
        self.session = requests.session()
        logging.debug(self.session)
        url = const.DOCKER_API_URL + const.D_API_AUTH
        r = self.get(url, params=params, auth=auth, timeout=30)

        decoded_request = self.json_decoder.decode(r.text)
        token = decoded_request['token']
        if const.DEBUG.print_response:
            logging.debug('== 3 headers ==')
            logging.debug(r.headers)
            logging.debugprint('== 4 content in lines ==')
            self.print_content(r.content.splitlines())

        if const.DEBUG.print_decoded_response:
            logging.debug("== token: %s" % token)

        if r.status_code / 100 != 2:
            return None

        # self.auth_token = 'Bearer ' + token
        self.auth_token = 'Bearer ' + token
        # self.session.headers.update({'Authorization': self.auth_token})
        return self.session

    @staticmethod
    def print_content(content):
        i = 0
        for line in content:
            logging.debug("%d: %s" % (i, line))
            i += 1

    def get_repositories(self):
        url = const.DOCKER_API_URL + const.D_API_CATALOG
        r = self.get(url, timeout=30)
        if r.status_code >= 400:
            return
        decoded_request = self.json_decoder.decode(r.text)
        if const.DEBUG.print_processed_response:
            i = 0
            for rep in decoded_request['repositories']:
                print("%d: %s" % (i, rep))
                i += 1
        if len(decoded_request['repositories']) == 0:
            return None
        else:
            return decoded_request['repositories']

    def is_supported(self):
        url = const.DOCKER_API_URL
        #    print('request: (token: %s)' % token)
        r = self.get(url, timeout=30)
        success_status_code = r.status_code / 100 == 2
        if const.DEBUG.print_processed_response or not success_status_code:
            logging.debug('== 3 headers ==')
            logging.debug(r.headers)
            logging.debug('== 4 content in lines ==')
            self.print_content(r.content.splitlines())
        return success_status_code

    def get_image_size(self, repo_name, image_id, b_decompress=False):
        size = 0
        try:
            url = const.DOCKER_API_URL + repo_name + '/blobs/' + image_id
            r = self.head(url, timeout=30)
            logging.debug(r.headers)
            if r.status_code / 100 == 2:
                size = int(r.headers['Content-Length'])
        except Exception as e:
            logging.error('Error issuing HEAD request ' + url)
            logging.error(' ==> %s' % e.args)
        return size

    def download_image(self, repo_name, image_id, b_decompress=False):
        url = const.DOCKER_API_URL + repo_name + '/blobs/' + image_id
        r = self.get(url, timeout=30)
        data = None
        size = 0
        if r.headers['Content-Encoding'] == 'gzip':
            bio = BytesIO(r.content)
            size = bio.seek(0, SEEK_END)
            logging.debug('compressed size = %d' % int(size))
            if b_decompress:
                bio.seek(0)
                data = gzip.decompress(bio.read())
                if const.Debug.print_processed_response:
                    logging.debug(" decoding gzip response")
                    logging.debug("Decompressed size = %d" % len(data))
                    logging.debug(data[:64])
            # data1 = str(data, 'utf-8')
            # print(data1[:64])
        return data, size

    def get_tags_in_repo(self, repo_name):
        url = const.DOCKER_API_URL + repo_name + '/tags/list'
        r = self.get(url, timeout=30)
        success = r.status_code / 100 == 2
        tags = []
        if success:
            decoded_request = self.json_decoder.decode(r.text)
            if len(decoded_request['tags']) > 0:
                for tag in decoded_request['tags']:
                    tags.append(tag)
            if const.DEBUG.print_processed_response:
                logging.debug('Tags for repo %s:' % repo_name)
                logging.debug('  %s' % tags)
        return success, tags

    def get_manifest_by_tag(self, repo_name, tag):
        url = const.DOCKER_API_URL + repo_name + '/manifests/' + tag
        r = self.get(url, timeout=30)
        decoded_request = self.json_decoder.decode(r.text)
        digests = []
        for line in decoded_request['fsLayers']:
            digests.append(line['blobSum'])
            if const.DEBUG.print_debug_info:
                logging.debug('appending ' + line['blobSum'])

        if const.DEBUG.print_processed_response:
            logging.debug('Digests for repo/tag %s/%s:' % (repo_name, tag))
            logging.debug('  %s' % digests)

        return digests

    def pull_all_images(self, repo_name, min_download_size = 50 * 1024):
        const.DEBUG.push_add_debug_info()
        success, tags = self.get_tags_in_repo(repo_name)
        tc = timer_class.TimerAPI()
        tc.start()

        if success:
            tag_iter = random_iter.RandomIter()
            digest_iter = random_iter.RandomIter()
            tag_iter.init(len(tags))
            next_tag_idx = tag_iter.next()
            while next_tag_idx is not None:
                tag = tags[next_tag_idx]
                digests = self.get_manifest_by_tag(repo_name, tag)
                for d in digests:
                    if const.Debug.print_debug_info:
                        logging.debug('Digest: %s' % d)
                i = 1
                # now = datetime.datetime.now()
                digest_iter.init(len(digests))
                next_digest_idx = digest_iter.next()
                #for digest in digests:
                while next_digest_idx is not None:
                    digest = digests[next_digest_idx]
                    size = self.get_image_size(repo_name, digest)
                    logging.debug(' image size=%d' % int(size))
                    if size > min_download_size:
                        start_download = timer_class.TimerAPI()
                        start_download.start()
                        logging.info(" Going to download image, size=%d" % size)
                        _, size = self.download_image(repo_name, digest)
                        dl_time_millis = start_download.diff_in_millis()
                        tc.add_stat(dl_time_millis, size)
                        i += 1
                    next_digest_idx = digest_iter.next()
                next_tag_idx = tag_iter.next()
        const.DEBUG.pop_debug_level()
        tc.print_stats()
        return tc.bandwidth()
