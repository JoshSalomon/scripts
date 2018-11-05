# import json
import sys
import datetime

from quay_constants import TEST_USERNAME, TEST_PWD, TEST_TAG, DEBUG
# import html
# from protocol_v2 import V2Protocol

# from docker_v2_apis import login, print_content, get_repositories
from docker_v2_apis import DockerV2Apis
from quay_apis import QuayApis

# import quay_constants as const

try:
    import requests
except ImportError as ie:
    print(ie)
    print("Error importing requests <%s, %s>" % (ie.name, ie.path))
    requests = None
    sys.exit(0)


#
# composite constants
#


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
#         print('== 4 text ==')
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


def run_main():
    # json_decoder = json.JSONDecoder()

    # image_id = const.IMAGE_ID_TOP
    # ancestors_list = get_image_ancestors(image_id).split('/')
    # print_ancestors_list(ancestors_list, image_id)

    # for anc in ancestors_list:
    #     if anc != '':
    #         new_list = get_image_ancestors(anc).split('/')
    #         print_ancestors_list(new_list, anc)

    # get_supported_apis(True)
    # get_image_manifest(True)

    docker_apis = DockerV2Apis()
    try:
        session = docker_apis.login(TEST_USERNAME, TEST_PWD, requests, False)

        quay_apis = QuayApis(session)

        supported = docker_apis.is_supported(False)
        if supported:
            print("Docker V2 APIs present")
        else:
            print("Failed to connect to Docker V2 API - exiting")
            exit(1)
        repos = docker_apis.get_repositories()
        if repos is None:
            print("No available repositories")
            exit(0)
        else:
            print("Some repositories are available")
        #
        # get the first repository
        #
        for i in range(2):
            repo_name = repos[i]
            print('repo %d: %s' % (i, repo_name))
            # images = quay_apis.get_images_in_repo(repo_name)
            # if len(images) > 0:
            #     for j in range(len(images)):
            #         if len(images[j]) > 60:
            #             docker_apis.download_image(repo_name, images[j])
            #             break
            success, tags = docker_apis.get_tags_in_repo(repo_name)
            digests = []
            if success:
                print(tags)
                if len(tags) > 0:
                    for tag in tags:
                        if tag == TEST_TAG:
                            digests = docker_apis.get_manifest_by_tag(repo_name, tag)
                            for d in digests:
                                print("Digest " + d)
                    i = 1
                    images = quay_apis.get_images_in_repo(repo_name)
                    for image in images:
                        print("Image " + image)
                        #todo write an API for getting image info and see if teh digest appears in the
                        #todo "command" field of the returned info
                    if i <= 3 and DEBUG:
                        now = datetime.datetime.now()
                        for digest in digests:
                            fname = f'image-{now.day}-{now.month}-{now.year}_{now.hour}{now.minute}{now.second}-{i}'
                            print("image # %d:" % i)
                            data = docker_apis.download_image(repo_name, digest)
                            i += 1
                            f = open('/home/jsalomon/PycharmProjects/Quay-test/Files/' + fname, 'wb+')
                            f.write(data)
                            f.flush()
                            f.close()


    except Exception as e:
        print(" Exception: <%s>" % e.__str__())
        print(" == Cause: <%s>" % e.__cause__)
        print(" == Context <%s>" % e.__context__)
        for arg in e.args:
            print(" == args <%s>" % arg)
        exit(1)

    exit(0)


if __name__ == "__main__":
    # execute only if run as a script
    run_main()
