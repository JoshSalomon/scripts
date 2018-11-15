
import threading
import logging

from quay_constants import TEST_USERNAME, TEST_PWD
from docker_v2_apis import DockerV2Apis

try:
    import requests
except ImportError as ie:
    print(ie)
    print("Error importing requests <%s, %s>" % (ie.name, ie.path))
    requests = None
    exit(0)


class Worker(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.bandwidth = 0
        self.total_capacity = 0

    def run(self):
        logging.debug('Start worker')
        docker_apis = DockerV2Apis()
        try:
            session = docker_apis.login(None, None, requests)

            # quay_apis = QuayApis(session)
            #
            supported = docker_apis.is_supported()
            if supported:
                logging.debug("Docker V2 APIs present")
            else:
                logging.error("Failed to connect to Docker V2 API - exiting")
                exit(1)
            repos = docker_apis.get_repositories()
            if repos is None:
                logging.warning("No available repositories")
                exit(0)
            else:
                logging.debug("Some repositories are available")
            #
            # get the first repository
            #
            i = 0
            for repo_name in repos:
                # repo_name = repos[i]
                logging.info('repo %d: %s' % (i, repo_name))
                i += 1
                self.bandwidth, self.total_capacity = docker_apis.pull_all_images(repo_name)

        except Exception as e:
            logging.error(" Exception: <%s>" % e.__str__())
            logging.error(" == Cause: <%s>" % e.__cause__)
            logging.error(" == Context <%s>" % e.__context__)
            for arg in e.args:
                logging.error(" == args <%s>" % arg)
            logging.error('Exit worker after exception, exit code 1')
            exit(1)

        logging.debug('return from worker')
        return

    def get_bandwidth(self):
        return self.bandwidth, self.total_capacity
