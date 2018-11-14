
import sys
import logging

import timer_class
import worker

NUM_THREADS = 2
# import quay_constants as const

try:
    import requests
except ImportError as ie:
    print(ie)
    print("Error importing requests <%s, %s>" % (ie.name, ie.path))
    requests = None
    sys.exit(0)

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


def wait_for_all_threads(threads):
    for t in threads:
        t.join()
    return


def run_main(num_threads: int = NUM_THREADS):
    logging.basicConfig(level=logging.INFO, format='[%(levelname)-8s] (%(threadName)-10s) %(message)s',)
    threads = []
    tc = None
    try:
        for i in range(num_threads):
            t = worker.Worker('Thread-%d' % i)
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
    #todo:
    #  do a proper upper and lower bounds of the stats (by taking the time of the fastest and slowest threads.
    #  - make sure the number is not an over estimation.
    time_in_millis = tc.diff_in_millis()
    lower_bound_bw = (total_cap / 1024) / (time_in_millis / 1000)
    logging.info("Done, total bandwidth = %d KB/s" % total_bw)
    logging.info("Total time: %d ms, lower bound bandwidth = %d KB/s" % (time_in_millis, int(lower_bound_bw)))
    exit(0)


if __name__ == "__main__":
    # execute only if run as a script
    run_main(NUM_THREADS)
