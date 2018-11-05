# import json
import os
# from requests import Session
import quay_constants as const
from abstract_api import AbstractAPIs
import gzip
from io import BytesIO
# from quay_constants import QUAY_URL, QUAY_DOMAIN


class DockerV2Apis(AbstractAPIs):
    def __init__(self):
        super().__init__()

    def login(self, username, pwd, requests, to_print_response):
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
        print(self.session)
        url = const.DOCKER_API_URL + const.D_API_AUTH
        print(url)
        r = self.get(url, params=params, auth=auth, timeout=30)

        if to_print_response:
            print(r)
        print('== Login status code: %d' % r.status_code)

        decoded_request = self.json_decoder.decode(r.text)
        token = decoded_request['token']
        if to_print_response:
            print('== 2 status code ==')
            print(r.status_code)
            print('== 3 headers ==')
            print(r.headers)
            print('== 4 content in lines ==')
            self.print_content(r.content.splitlines())
            print("== token: %s" % token)

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
            print("%d: %s" % (i, line))
            i += 1

    def get_repositories(self):
        url = const.DOCKER_API_URL + const.D_API_CATALOG
        print(url)
        r = self.get(url, timeout=12)
        print("Getting catalog, rc=%d" % r.status_code)
        print(r.text)
        if r.status_code >= 400:
            return
        decoded_request = self.json_decoder.decode(r.text)
        i = 0
        for rep in decoded_request['repositories']:
            print("%d: %s" % (i, rep))
            i += 1
        if len(decoded_request['repositories']) == 0:
            return None
        else:
            return decoded_request['repositories']

    def is_supported(self, to_print_response):
        url = const.DOCKER_API_URL
        #    print('request: (token: %s)' % token)
        print(url)
        r = self.get(url, timeout=12)
        success_status_code: bool = r.status_code / 100 == 2
        print(r)
        if to_print_response or not success_status_code:
            print('== 2 status code ==')
            print(r.status_code)
            print('== 3 headers ==')
            print(r.headers)
            print('== 4 content in lines ==')
            self.print_content(r.content.splitlines())
        return success_status_code

    def download_image(self, repo_name, image_id):
        url = const.DOCKER_API_URL + repo_name + '/blobs/' + image_id
        print(url)
        r = self.get(url, timeout=12)
        print(r)
        print(r.headers)
        # print(r.content)
        print(str(r.headers))
        data = None
        if r.headers['Content-Encoding'] == 'gzip':
            print(" decoding gzip response")
            bio = BytesIO(r.content)
            bio.seek(0)
            data = gzip.decompress(bio.read())
            print("Decompressed size = %d" % len(data))
            print(data[:64])
            # data1 = str(data, 'utf-8')
            # print(data1[:64])
        return data

    def get_tags_in_repo(self, repo_name):
        url = const.DOCKER_API_URL + repo_name + '/tags/list'
        print(url)
        r = self.get(url, timeout=12)
        success = r.status_code / 100 == 2
        print(r)
        print(r.text)
        tags = []
        if success:
            decoded_request = self.json_decoder.decode(r.text)
            if len(decoded_request['tags']) > 0:
                for tag in decoded_request['tags']:
                    tags.append(tag)
        return success, tags

    def get_manifest_by_tag(self, repo_name, tag):
        url = const.DOCKER_API_URL + repo_name + '/manifests/' + tag
        print('request:')
        print(url)
        r = self.get(url, timeout=12)
        print(r.status_code)
        print(r.text)
        decoded_request = self.json_decoder.decode(r.text)
        digests = []
        for line in decoded_request['fsLayers']:
            digests.append(line['blobSum'])
            print('appending ' + line['blobSum'])

        return digests
