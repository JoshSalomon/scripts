# import json
import os
import datetime
# from requests import Session
import quay_constants as const
from abstract_api import AbstractAPIs
import gzip
from io import BytesIO, SEEK_END
import timer_class


# from quay_constants import QUAY_URL, QUAY_DOMAIN


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
        print(self.session)
        url = const.DOCKER_API_URL + const.D_API_AUTH
        r = self.get(url, params=params, auth=auth, timeout=30)

        decoded_request = self.json_decoder.decode(r.text)
        token = decoded_request['token']
        if const.DEBUG.print_response:
            print('== 3 headers ==')
            print(r.headers)
            print('== 4 content in lines ==')
            self.print_content(r.content.splitlines())

        if const.DEBUG.print_decoded_response:
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
        r = self.get(url, timeout=12)
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
        r = self.get(url, timeout=12)
        success_status_code: bool = r.status_code / 100 == 2
        if const.DEBUG.print_processed_response or not success_status_code:
            print('== 3 headers ==')
            print(r.headers)
            print('== 4 content in lines ==')
            self.print_content(r.content.splitlines())
        return success_status_code

    def download_image(self, repo_name, image_id, b_decompress=False):
        url = const.DOCKER_API_URL + repo_name + '/blobs/' + image_id
        r = self.get(url, timeout=12)
        data = None
        size = 0
        if r.headers['Content-Encoding'] == 'gzip':
            bio = BytesIO(r.content)
            size = bio.seek(0, SEEK_END)
            print(f'compressed size = {size}')
            if b_decompress:
                bio.seek(0)
                data = gzip.decompress(bio.read())
                if const.Debug.print_processed_response:
                    print(" decoding gzip response")
                    print("Decompressed size = %d" % len(data))
                    print(data[:64])
            # data1 = str(data, 'utf-8')
            # print(data1[:64])
        return data, size

    def get_tags_in_repo(self, repo_name):
        url = const.DOCKER_API_URL + repo_name + '/tags/list'
        r = self.get(url, timeout=12)
        success = r.status_code / 100 == 2
        tags = []
        if success:
            decoded_request = self.json_decoder.decode(r.text)
            if len(decoded_request['tags']) > 0:
                for tag in decoded_request['tags']:
                    tags.append(tag)
            if const.DEBUG.print_processed_response:
                print(f'Tags for repo {repo_name}:')
                print(f'  {tags}')
        return success, tags

    def get_manifest_by_tag(self, repo_name, tag):
        url = const.DOCKER_API_URL + repo_name + '/manifests/' + tag
        r = self.get(url, timeout=12)
        decoded_request = self.json_decoder.decode(r.text)
        digests = []
        for line in decoded_request['fsLayers']:
            digests.append(line['blobSum'])
            if const.DEBUG.print_debug_info:
                print('appending ' + line['blobSum'])

        if const.DEBUG.print_processed_response:
            print(f'Digests for repo/tag {repo_name}/{tag}:')
            print(f'  {digests}')

        return digests

    def pull_all_images(self, repo_name):
        const.DEBUG.push_add_debug_info()
        success, tags = self.get_tags_in_repo(repo_name)
        tc = timer_class.TimerAPI()
        tc.start()
        if success:
            for tag in tags:
                digests = self.get_manifest_by_tag(repo_name, tag)
                for d in digests:
                    if const.Debug.print_debug_info:
                        print(f'Digest: {d}')
                i = 1
                # now = datetime.datetime.now()
                for digest in digests:
                    # fname = f'image-{now.day}-{now.month}-{now.year}_{now.hour}{now.minute}{now.second}-{i}'
                    if const.Debug.print_debug_info:
                        print("image # %d:" % i)
                    start_download = timer_class.TimerAPI()
                    start_download.start()
                    _, size = self.download_image(repo_name, digest)
                    dl_time_millis = start_download.diff_in_millis()
                    tc.add_stat(dl_time_millis, size)
                    i += 1
                    # f = open('/home/jsalomon/PycharmProjects/Quay-test/Files/' + fname, 'wb+')
                    # f.write(data)
                    # f.flush()
                    # f.close()
        const.DEBUG.pop_debug_level()
        tc.print_stats()
