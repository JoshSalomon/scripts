
class DockerImage(object):
    def __init__(self, manifest, checksum, image_bytes, layer_dict, tag):
        self.__manifest__ = manifest
        self.__checksum__ = checksum
        self.__image_bytes__ = image_bytes
        self.__layer_dict__ = layer_dict
        self.__tag__ = tag

    def __del__(self):
        del self.__image_bytes__
        del self.__layer_dict__
        del self.__manifest__

    @property
    def manifest(self):
        return self.__manifest__

    @property
    def checksum(self):
        return self.__checksum__

    @property
    def image_bytes(self):
        return self.__image_bytes__

    @property
    def layer_dict(self):
        return self.__layer_dict__

    @property
    def tag(self):
        return self.__tag__

    @property
    def size(self):
        return self.layer_dict['Size']
