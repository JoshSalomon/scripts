
import quay_constants as const
import config
from abstract_api import AbstractAPIs
from docker_v2_apis import DockerV2Apis

c = config.Config()


class QuayApis(AbstractAPIs):
    def __init__(self, session):
        super().__init__(session)
        self.auth_token = 'Bearer ' + const.QUAY_API_TOKEN

    #     self.session = session
    #     self.json_decoder = json.JSONDecoder()

    def get_image_ancestors(self, repo_name, img_id):
        params = {
            'account': c.username,
            'service': c.docker_api_domain(),
            'scope': [],
        }
        url = const.QUAY_API_URL + const.Q_API_REPOSITORY + '/' + repo_name + '/image/' + img_id
        print('request:')
        print(url)
        r = self.get(url, headers={'Accept-encoding': 'gzip'}, timeout=12, params=params)
        print(r)
        print('== 2 status code ==')
        print(r.status_code)
        print('== 3 headers ==')
        print(r.headers)
        print('== 4 text ==')
        # print(r.text)
        # print('== 5 content ==')
        # print(r.content)

        print('== 6 contents in lines ==')
        DockerV2Apis.print_content(r.content.splitlines())
        decoded_request = self.json_decoder.decode(r.text)
        ancestors = decoded_request['ancestors']
        return ancestors

    def get_images_in_repo(self, repo_name):
        url = const.QUAY_API_URL + const.Q_API_REPOSITORY + '/' + repo_name + '/image/'
        print('request:')
        print(url)
        r = self.get(url, timeout=12)
        decoded_request = self.json_decoder.decode(r.text)
        images = []
        for img_md in decoded_request['images']:
            print(img_md)
            print('%s %s %d' % (img_md['id'], img_md['created'], img_md['size']))
            images.append(img_md['id'])
        return images

