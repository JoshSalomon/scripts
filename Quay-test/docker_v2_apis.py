import quay_constants as const
from abstract_api import AbstractAPIs
import gzip
from io import BytesIO, SEEK_END
import timer_class
import random_iter
import logging
import requests
import time

import config
import docker_image

c = config.Config()


class TestTimeExpired(Exception):
    def __init__(self):
        pass


class DockerV2Apis(AbstractAPIs):
    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address

    def login(self, scopes=None):
        if scopes is None:
            scopes = []
        params = {
            'account': c.username,
            'service': c.docker_api_domain(self.ip_address),
            'scope': scopes,
        }
        auth = (c.username, c.password)
        self.session = requests.Session()
        logging.debug(self.session)
        url = c.docker_api_url(self.ip_address) + const.D_API_AUTH
        # todo - put try/except around this and handle rc 500 some way.

        max_retries = 5
        r = None
        for i in range(max_retries):
            try:
                r = self.get(url, params=params, auth=auth, timeout=30)
                break   # if no exception was raised, continue.
            except const.AppRetryException as ar:
                if i < (max_retries - 1):
                    logging.info(f"Login failed, rc={ar.__status_code__} - waiting and retrying")
                    time.sleep(1)
                    continue
                else:
                    logging.error(f"Failed {max_retries} login attempts, quitting")
                    raise ar

        if r is None or r.status_code / 100 != 2:
            raise const.HttpAppException(f" Login failed, rc={r.status_code}", r.status_code, r.text)

        token = ""
        if r is not None and r.headers['Content-Type'] == 'application/json':
            decoded_request = self.json_decoder.decode(r.text)
            token = decoded_request['token']
            if const.DEBUG.print_response:
                logging.debug('== 3 headers ==')
                logging.debug(r.headers)
                logging.debug('== 4 content in lines ==')
                self.print_content(r.content.splitlines())

            if const.DEBUG.print_decoded_response:
                logging.debug("== token: %s" % token)

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
        url = c.docker_api_url(self.ip_address) + const.D_API_CATALOG
        r = self.get(url, timeout=30)
        if r.status_code >= 400:
            return
        decoded_request = self.json_decoder.decode(r.text)
        if const.DEBUG.print_processed_response:
            i = 1
            nreps = len(decoded_request['repositories'])
            for rep in decoded_request['repositories']:
                if i == 1:
                    logging.debug('List of repositories')
                logging.debug(" * %d/%d: %s" % (i, nreps, rep))
                i += 1
        if len(decoded_request['repositories']) == 0:
            return None
        else:
            return decoded_request['repositories']

    def is_supported(self):
        url = c.docker_api_url(self.ip_address)
        #    print('request: (token: %s)' % token)
        r = self.get(url, timeout=30)
        success_status_code = r.status_code / 100 == 2
        if const.DEBUG.print_processed_response or not success_status_code:
            logging.debug('== 3 headers ==')
            logging.debug(r.headers)
            logging.debug('== 4 content in lines ==')
            self.print_content(r.content.splitlines())
        return success_status_code

    def get_image_size(self, repo_name, image_id):
        size = 0
        url = c.docker_api_url(self.ip_address) + repo_name + '/blobs/' + image_id
        retry = True
        while retry:
            try:
                r = self.head(url, timeout=30)
                retry = False
                logging.debug(r.headers)
                if r.status_code / 100 == 2:
                    size = int(r.headers['Content-Length'])
            except const.AppRetryException as are:
                if are.do_relogin:
                    logging.debug(f' Expired token, doing re-login and retry')
                    scopes = [f'repository:{const.TEST_USERNAME}/test1:*']
                    self.login(scopes=scopes)
                retry = True
            except Exception as e:
                logging.error('Error issuing HEAD request ' + url)
                logging.error(' ==> %s' % e.args)
        return size

    def download_image(self, repo_name, image_id, b_decompress=False):
        url = c.docker_api_url(self.ip_address) + repo_name + '/blobs/' + image_id
        r = self.get(url, timeout=300, headers={'Accept-encoding': 'gzip, application/octet-stream'})
        data = None
        size = 0
        # noinspection PyBroadException
        try:
            if r.headers['Content-Encoding'] == 'gzip':
                bio = BytesIO(r.content)
                size = bio.seek(0, SEEK_END)
                logging.debug('Compressed size = %d' % int(size))
                if b_decompress:
                    bio.seek(0)
                    data = gzip.decompress(bio.read())
                    if const.Debug.print_processed_response:
                        logging.debug("Decompressed size = %d" % len(data))
                        logging.debug(data[:64])
        except Exception:
            size = r.headers['Content-Length']
            # data1 = str(data, 'utf-8')
            # print(data1[:64])
        return data, size

    def get_tags_in_repo(self, repo_name):
        url = c.docker_api_url(self.ip_address) + repo_name + '/tags/list'
        tags = []
        success = True
        verbose_get = True
        while url is not None and url != "":
            retry = True
            success = True
            niter = 1
            while retry:
                try:
                    r = self.get(url, b_verbose=verbose_get, timeout=30)
                    niter += 1
                    retry = False
                    verbose_get = False
                    success = r.status_code / 100 == 2
                    if success:
                        decoded_request = self.json_decoder.decode(r.text)
                        if len(decoded_request['tags']) > 0:
                            for tag in decoded_request['tags']:
                                tags.append(tag)
                        if const.DEBUG.print_processed_response:
                            ltags = len(tags)
                            if ltags % 2500 == 0:
                                logging.info(f'Read {ltags:,} tags from repo {repo_name}')
                            elif ltags % 500 == 0:
                                logging.debug(f'Read {ltags:,} tags from repo {repo_name}')
                            # logging.debug('  %s' % tags)
                        try:
                            next_url = r.headers['Link']
                        except KeyError:
                            next_url = None
                        if c.max_tags > 0:
                            if len(tags) >= c.max_tags:
                                logging.debug(f' Got {len(tags)}, skipping reading tags')
                                next_url = None
                        if next_url is not None and next_url != "":
                            assert len(next_url) > 13
                            assert next_url[:5] == '</v2/'
                            assert next_url[-13:] == '>; rel="next"'
                            url = c.docker_api_url(self.ip_address) + next_url[5:-13]
                        else:
                            if len(tags) < 50:
                                logging.debug(f'  {tags}')
                            else:
                                logging.debug(f'  {tags[:20]}')
                                logging.debug(f' .... {len(tags)-40} tags skipped ...')
                                logging.debug(f'  {tags[-20:]}')
                            url = None
                    else:
                        url = None

                except const.AppRetryException as are:
                    if are.do_relogin:
                        logging.debug(f' Expired token, doing re-login and retry')
                        scopes = [f'repository:{const.TEST_USERNAME}/test1:*']
                        self.login(scopes=scopes)
                    retry = True

        return success, tags

    def get_manifest_by_tag(self, repo_name, tag):
        url = c.docker_api_url(self.ip_address) + repo_name + '/manifests/' + tag
        r = self.get(url, timeout=30)
        if r.status_code / 100 == 5:
            return []

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

    def patch_image_in_chunks(self, url, dckr_image: docker_image.DockerImage, headers):
        chunk_size = c.push_chunk_size
        assert chunk_size > 0
        i = 0
        start_byte = 0
        logging.debug(f" *** Going to push image in chunks - image size={dckr_image.size}")
        logging.debug(f" *** Going to use {int(dckr_image.size/chunk_size)} chunks")
        while start_byte < dckr_image.size:
            end_byte = min(start_byte + chunk_size, dckr_image.size)
            patch_header = {'Range': f'bytes={start_byte}-{end_byte}'}
            patch_header.update(headers)
            content_chunk = dckr_image.image_bytes[start_byte:end_byte]
            r = self.patch(url, data=content_chunk, headers=patch_header)
            logging.debug(f"==> Uploaded chunk {i}, status={r.status_code}")
            i = i + 1
            failure = int(r.status_code / 100) != 2
            if failure:
                logging.error(f'Failed loading the image bytes, chunk #{i}, size{dckr_image.size}: rc={r.status_code}')
                logging.error(r.headers)
                logging.error(r.content)
                raise const.HttpAppException(f'Failed loading image bytes, (chunk {i}) rc={r.status_code}',
                                             r.status_code, r.text)
            start_byte = start_byte + chunk_size
        return

    def push_single_image(self, repo_name, dckr_image: docker_image.DockerImage, header=None):
        #
        # upload is a 2 phase process, first POST a message to the blobs/uploads API
        # then get a url into which we need to PATCH the image
        #
        url = c.docker_api_url(self.ip_address) + repo_name + '/blobs/uploads/'
        r = self.post(url, timeout=12)
        failure = int(r.status_code / 100) != 2
        if failure:
            logging.error(f'**Failed to start upload rc={r.status_code}')
            logging.error(r.headers)
            logging.error(r.content)
            raise const.HttpAppException(f'Failed starting upload, rc={r.status_code}', r.status_code, r.text)
        upload_uuid = r.headers['Docker-Upload-UUID']
        new_upload_location = r.headers['Location']
        logging.debug(f'Starting upload {upload_uuid} to {new_upload_location}')
        # phase 2 starts here...
        self.patch_image_in_chunks(new_upload_location, dckr_image, header)
        # r = self.patch(new_upload_location, data=dckr_image.image_bytes, headers=header, timeout=3000)

        # Complete the process by the final message
        r = self.put(new_upload_location, params=dict(digest=dckr_image.checksum))
        failure = int(r.status_code / 100) != 2
        if failure:
            logging.error(f'Failed adding the digest, rc={r.status_code}')
            logging.error(r.headers)
            logging.error(r.content)
            raise const.HttpAppException(f'Failed adding the digest, rc={r.status_code}', r.status_code, r.text)

        assert r.headers['Docker-Content-Digest'] == dckr_image.checksum
        # todo - add here head command for checking the upload.

        # Last phase - write the manifest
        manifest_headers = {'Content-Type': 'application/json'}
        manifest_headers.update(header)
        url = c.docker_api_url(self.ip_address) + repo_name + f'/manifests/{dckr_image.tag}'
        logging.debug(dckr_image.manifest.json)
        r = self.put(url, data=dckr_image.manifest.json, headers=manifest_headers)
        failure = int(r.status_code / 100) != 2
        if failure:
            logging.error(f'Failed adding the manifest, rc={r.status_code}')
            logging.error(r.headers)
            logging.error(r.content)

    # todo make min download size configurable from command line.
    def pull_all_images(self, repo_name, min_download_size=50 * 1024):
        global digest
        const.DEBUG.push_add_debug_info()
        success, tags = self.get_tags_in_repo(repo_name)
        tc = timer_class.TimerAPI()
        tc.start()
        retry_count = 0
        if success:
            try:
                for i in range(c.cycles):
                    logging.info(f" Cycle {i+1}/{c.cycles}: repo: {repo_name}")
                    tag_iter = random_iter.RandomIter()
                    digest_iter = random_iter.RandomIter()
                    tag_iter.init(len(tags))
                    logging.info(f"Found {len(tags)} tags in repo {repo_name}")
                    next_tag_idx = tag_iter.next()
                    while next_tag_idx is not None:
                        tag = tags[next_tag_idx]
                        next_tag_idx = tag_iter.next()
                        try:
                            digests = self.get_manifest_by_tag(repo_name, tag)
                        except const.AppRetryException:
                            logging.info(f' skipping tag {tag}')
                            continue

                        for d in digests:
                            if const.Debug.print_debug_info:
                                logging.debug('Digest: %s' % d)
                        i = 1
                        # now = datetime.datetime.now()
                        digest_iter.init(len(digests))
                        next_digest_idx = digest_iter.next()
                        # for digest in digests:
                        while next_digest_idx is not None:
                            retry = True
                            while retry:
                                try:
                                    digest = digests[next_digest_idx]
                                    size = self.get_image_size(repo_name, digest)
                                    logging.debug(' image size=%d' % int(size))
                                    if size > min_download_size:
                                        start_download = timer_class.TimerAPI()
                                        start_download.start()
                                        logging.info(" <{}> Going to download image, size={:,} tag={}".format
                                                     (tc.diff_in_seconds(), size, tag))
                                        _, size = self.download_image(repo_name, digest)
                                        # it becomes larger only when exceptions are raised in download_image
                                        retry_count = 0
                                        dl_time_millis = start_download.diff_in_millis()
                                        tc.add_stat(dl_time_millis, size)
                                        i += 1
                                        if c.wait_between_ops > 0:
                                            time.sleep(c.wait_between_ops)
                                    if tc.diff_in_millis() > c.millis_to_end:
                                        logging.info("Finish test after {:,} ms, threshold is {:,} ms".format
                                                     (tc.diff_in_millis(), c.millis_to_end))
                                        raise TestTimeExpired()
                                    next_digest_idx = digest_iter.next()
                                    retry = False
                                except const.AppRetryException as are:
                                    if retry_count < 5:
                                        retry_count += 1
                                        if are.do_relogin:
                                            logging.debug(f' Expired token, doing re-login and retry')
                                            scopes = [f'repository:{const.TEST_USERNAME}/test1:*']
                                            self.login(scopes=scopes)
                                            retry = True
                                        else:
                                            logging.info(f' Skipping tag {tag} / digest {digest} ')
                                            retry = False
                                    else:
                                        raise are
            except TestTimeExpired:
                pass
        const.DEBUG.pop_debug_level()

        tc.print_stats()
        return tc.bandwidth()
