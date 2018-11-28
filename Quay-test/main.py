
import sys
import logging

import timer_class
import worker
import pusher
import config
import quay_constants as const
import docker_v2_apis as docker_apis

# import quay_constants as const

try:
    import requests
except ImportError as ie:
    print(ie)
    print("Error importing requests <%s, %s>" % (ie.name, ie.path))
    requests = None
    sys.exit(0)

config = config.Config()
# def get_image_ancestors(img_id):
#     url = const.QUAY_API_URL + '/' + const.NAMESPACE + '/' + const.REPOSITORY + '/image/' + img_id
#     print('request:')
#     print(url)
#     r = requests.get(url, headers={'Accept-encoding': 'gzip'}, timeout=12)
#     print(r)
#     print('== 2 status code ==')
#     print(r.status_code)
#     print('== 3 headers ==')
#     print(r.headers)
#     print('== 4 text ==')
#     # print(r.text)
#     # print('== 5 content ==')
#     # print(r.content)
#     print('== 6 contents in lines ==')
#     DockerV2Apis.print_content(r.content.splitlines())
#     decoded_request = json_decoder.decode(r.text)
#     ancestors = decoded_request['ancestors']
#     return ancestors


# def print_ancestors_list(a_list: str, image_id: str):
#     print('Ancestors of ' + image_id)
#     for anc in a_list:
#         if anc != '':
#             print(" ==> " + anc)


# def get_supported_apis(to_print_response):
#     url = const.QUAY_REPO_API_URL
#     print('request:')
#     print(url)
#     r = requests.get(url, headers={'Accept-encoding': 'gzip'}, timeout=12)
#     print(r)
#     print('== 2 status code ==')
#     print(r.status_code)
#     if to_print_response:
#         print('== 3 headers ==')
#         print(r.headers)
#          print('== 4 text ==')
#         print(r.text)
#         # print('== 5 content ==')
#         # print(r.content)
#         print('== 6 contents in lines ==')
#         print_content(r.content.splitlines())


# def get_image_manifest(to_print_response):
#     url = const.QUAY_REPO_API_URL + '/' + const.REPOSITORY + '/manifests/' + const.IMAGE_ID_TOP
#     print('request:')
#     print(url)
#     r = requests.get(url, headers={'Accept-encoding': 'gzip'}, timeout=12)
#     if to_print_response:
#         print(r)
#         print('== 2 status code ==')
#         print(r.status_code)
#         print('== 3 headers ==')
#         print(r.headers)
#         print('== 4 content in lines ==')
#         print_content(r.content.splitlines())

def start_all_threads(threads):
    for t in threads:
        t.start()
    return


def wait_for_all_threads(threads, push_threads=[]):
    for t in threads:
        if isinstance(t, worker.Worker):
            t.join()

    for pt in push_threads:
        if isinstance(pt, pusher.Pusher):
            pt.__stop_event__.set()
            pt.join()

    return


def run_prep(n_threads=0):
    ip = ""
    credentials = []
    if n_threads <= 0:
        n_threads = config.threads
    for i in range(n_threads):
        try:
            ip = const.QUAY_DOMAINS[i % len(const.QUAY_DOMAINS)]
            d_api = docker_apis.DockerV2Apis(ip)
            session = d_api.login()
            logging.debug(f"Logging to {ip}, session=<{session}>, stat")
            credentials.append((ip, d_api))
        except const.AppException as ae:
            #
            # login failed
            #
            logging.info(f"Failed logging in to server {ip} - msg: {ae.__msg__}")
    return credentials


def test_push(credentials, repo_name):
    p = pusher.Pusher("thread-name", credentials, repo_name)
    p.push()
    return


#todo performance improvement:
# Create a pre-process stage that iterates over the repository and filters out the
# small images, leaving only the big ones - then the read all images can skip reading
# headers for all the small images
def run_main():
    if config.verbose:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO

    logging.basicConfig(level=lvl, format='[%(levelname)-8s] (%(threadName)-10s) %(message)s',)
    threads = []
    tc = None
    #credentials = run_prep()

    credentials = run_prep(1)
    test_push(credentials[0], 'test_runner/test1')
    exit(0)
    try:
        logging.info(f"Starting {config.threads} threads")
        for i in range(len(credentials)):
            t = worker.Worker('Thread-%d' % i, credentials[i])
            threads.append(t)
        start_all_threads(threads)
        tc = timer_class.TimerAPI()
        tc.start()
    except Exception as e:
        logging.error("Unable to start threads, %s" % e.args)
#        raise e

    logging.info("Waiting for thread to complete")
    wait_for_all_threads(threads)
    total_bw = 0
    total_cap = 0
    for t in threads:
        bw, cap = t.get_bandwidth()
        total_bw += bw
        total_cap += cap
        total_bw += bw
    #todo:
    #  do a proper upper and lower bounds of the stats (by taking the time of the fastest and slowest threads.
    #  - make sure the number is not an over estimation.
    time_in_millis = tc.diff_in_millis()
    if time_in_millis > 0:
        lower_bound_bw = (total_cap / 1024) / (time_in_millis / 1000)
        logging.info("Done, total bandwidth = %d KB/s (%d MB/s)" % (total_bw, int(total_bw / 1024)))
        if int(lower_bound_bw) < 20480:
            logging.info("Total time: %d ms, lower bound bandwidth = %d KB/s" % (time_in_millis, int(lower_bound_bw)))
        else:
            lower_bound_bw /= 1024
            logging.info("Total time: %d ms, lower bound bandwidth = %d MB/s" % (time_in_millis, int(lower_bound_bw)))
    exit(0)


if __name__ == "__main__":
    # execute only if run as a script - this is always debug run
    config.set_verbose(True)
    run_main()
