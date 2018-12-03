import tarfile
from io import StringIO, BytesIO
import random
import logging
import os
from jwt.utils import b64encode, b64decode
from jwkest.jws import SIGNER_ALGS, keyrep
from jwkest.jwk import RSAKey
import json
from jsonschema import ValidationError, validate as validate_schema
from collections import OrderedDict, namedtuple
import dateutil.parser

from datetime import datetime
import abc
from six import add_metaclass
import hashlib
import re
import os.path

###
# This file contains multiple code excerpts from the quay test code. In order not to
# bring the entire test framework into this mini-project I copied just the pieces of
# code I think are used by the code I need - mainly in order to push large images
# into Quay repository - some of this code may be redundant and unused in this project.
###

# Content Types
DOCKER_SCHEMA1_MANIFEST_CONTENT_TYPE = 'application/vnd.docker.distribution.manifest.v1+json'
DOCKER_SCHEMA1_SIGNED_MANIFEST_CONTENT_TYPE = 'application/vnd.docker.distribution.manifest.v1+prettyjws'
DOCKER_SCHEMA1_CONTENT_TYPES = {DOCKER_SCHEMA1_MANIFEST_CONTENT_TYPE,
                                DOCKER_SCHEMA1_SIGNED_MANIFEST_CONTENT_TYPE}

# Keys for signature-related data
DOCKER_SCHEMA1_SIGNATURES_KEY = 'signatures'
DOCKER_SCHEMA1_HEADER_KEY = 'header'
DOCKER_SCHEMA1_SIGNATURE_KEY = 'signature'
DOCKER_SCHEMA1_PROTECTED_KEY = 'protected'
DOCKER_SCHEMA1_FORMAT_LENGTH_KEY = 'formatLength'
DOCKER_SCHEMA1_FORMAT_TAIL_KEY = 'formatTail'

# Keys for manifest-related data
DOCKER_SCHEMA1_REPO_NAME_KEY = 'name'
DOCKER_SCHEMA1_REPO_TAG_KEY = 'tag'
DOCKER_SCHEMA1_ARCH_KEY = 'architecture'
DOCKER_SCHEMA1_FS_LAYERS_KEY = 'fsLayers'
DOCKER_SCHEMA1_BLOB_SUM_KEY = 'blobSum'
DOCKER_SCHEMA1_HISTORY_KEY = 'history'
DOCKER_SCHEMA1_V1_COMPAT_KEY = 'v1Compatibility'
DOCKER_SCHEMA1_SCHEMA_VER_KEY = 'schemaVersion'

# Format for time used in the protected payload.
_ISO_DATETIME_FORMAT_ZULU = '%Y-%m-%dT%H:%M:%SZ'

# The algorithm we use to sign the JWS.
_JWS_SIGNING_ALGORITHM = 'RS256'


def layer_bytes_for_contents(contents, mode='|gz', other_files=None, binary_content=True):
    layer_data = StringIO()
    tar_file = tarfile.open(fileobj=layer_data, mode='w' + mode)

    def add_file(name, contents):
        tar_file_info = tarfile.TarInfo(name=name)
        tar_file_info.type = tarfile.REGTYPE
        tar_file_info.size = len(contents)
        tar_file_info.mtime = 1

        if binary_content:
            contents_stream = BytesIO(contents)
        else:
            contents_stream = StringIO(contents)
        assert contents_stream is not None
        assert isinstance(contents_stream, (BytesIO, StringIO))
        tar_file.addfile(tar_file_info, contents_stream)

    add_file('contents', contents)

    if other_files is not None:
        for file_name, file_contents in other_files.iteritems():
            add_file(file_name, file_contents)

    tar_file.close()

    layer_bytes = layer_data.getvalue()
    layer_data.close()
    return layer_bytes


def __create_blob__(min_size_bytes, max_size_bytes):
    # todo - improve a bit the distribution? Use normal distribution?
    size_bytes = random.randint(min_size_bytes, max_size_bytes)
    image_bytes: bytes = os.urandom(size_bytes)
    return image_bytes, size_bytes


def create_random_image(min_size_bytes, max_size_bytes, image_id='someid'):
    image_bytes, size_bytes = __create_blob__(min_size_bytes, max_size_bytes)
    logging.debug(f'Created image id:{image_id} - size {len(image_bytes)}')
    return {'id': image_id, 'contents': image_bytes, 'Size': size_bytes}


class DockerSchema1ManifestBuilder(object):
    """
    A convenient abstraction around creating new DockerSchema1Manifests.
    """

    def __init__(self, namespace_name, repo_name, tag, architecture='amd64'):
        repo_name_key = '{0}/{1}'.format(namespace_name, repo_name)
        if namespace_name == '':
            repo_name_key = repo_name

        self._base_payload = {
            DOCKER_SCHEMA1_REPO_TAG_KEY: tag,
            DOCKER_SCHEMA1_REPO_NAME_KEY: repo_name_key,
            DOCKER_SCHEMA1_ARCH_KEY: architecture,
            DOCKER_SCHEMA1_SCHEMA_VER_KEY: 1,
        }

        self._fs_layer_digests = []
        self._history = []

    def add_layer(self, layer_digest, v1_json_metadata):
        decoder = json.JSONDecoder()
        self._fs_layer_digests.append({
            DOCKER_SCHEMA1_BLOB_SUM_KEY: layer_digest,
        })

#        compatibility_str='{\"id\":\"%s\"'
        self._history.append({
            DOCKER_SCHEMA1_V1_COMPAT_KEY: v1_json_metadata,
#            DOCKER_SCHEMA1_V1_COMPAT_KEY: decoder.decode(v1_json_metadata),
        })
        return self

    def build(self, json_web_key):
        """
        Builds a DockerSchema1Manifest object complete with signature.
        """
        payload = OrderedDict(self._base_payload)
        payload.update({
            DOCKER_SCHEMA1_HISTORY_KEY: self._history,
            DOCKER_SCHEMA1_FS_LAYERS_KEY: self._fs_layer_digests,
        })

        payload_str = json.dumps(payload, indent=3)

        split_point = payload_str.rfind('\n}')

        protected_payload = {
            'formatTail': b64encode(payload_str[split_point:].encode('utf-8')),
            'formatLength': split_point,
            'time': datetime.utcnow().strftime(_ISO_DATETIME_FORMAT_ZULU),
        }
        protected = b64encode(json.dumps(protected_payload).encode('utf-8'))
        logging.debug('Generated protected block: %s', protected)

        str_to_sign = '{0}.{1}'.format(protected, b64encode(payload_str.encode('utf-8')))
        bytes_to_sign = bytes(str_to_sign, 'utf-8')

        signer = SIGNER_ALGS[_JWS_SIGNING_ALGORITHM]
#        signature = b64encode(signer.sign(bytes_to_sign, json_web_key.get_key()))
        # todo (low) - make it a separate function
        key = RSAKey(kty=json_web_key['kty'],
                     n=json_web_key['n'],
                     e=json_web_key['e'],
                     d=json_web_key['d'],
                     p=json_web_key['p'],
                     q=json_web_key['q'])
        key.deserialize()
        signature = b64encode(signer.sign(bytes_to_sign, key.get_key()))
#        signature = b64encode(signer.sign(bytes_to_sign, json_web_key.publickey()))
        logging.debug('Generated signature: %s', signature)

#        public_members = set(json_web_key.public_members)
#        public_key = {comp: value for comp, value in json_web_key.to_dict().items()
#                      if comp in public_members}

        public_key = key.serialize(False)
        signature_block = {
            DOCKER_SCHEMA1_HEADER_KEY: {'jwk': public_key, 'alg': _JWS_SIGNING_ALGORITHM},
            DOCKER_SCHEMA1_SIGNATURE_KEY: signature,
            DOCKER_SCHEMA1_PROTECTED_KEY: protected,
        }

        logging.debug('Encoded signature block: %s', json.dumps(signature_block))

        payload.update({DOCKER_SCHEMA1_SIGNATURES_KEY: [signature_block]})

        return DockerSchema1Manifest(json.dumps(payload, indent=3), validate=False)


def _updated_v1_metadata(v1_metadata_json, updated_id_map):
    """
    Updates v1_metadata with new image IDs.
    """
    parsed = json.loads(v1_metadata_json)
    parsed['id'] = updated_id_map[parsed['id']]

    if parsed.get('parent') and parsed['parent'] in updated_id_map:
        parsed['parent'] = updated_id_map[parsed['parent']]

    if parsed.get('container_config', {}).get('Image'):
        existing_image = parsed['container_config']['Image']
        if existing_image in updated_id_map:
            parsed['container_config']['image'] = updated_id_map[existing_image]

    return json.dumps(parsed)


class DockerFormatException(Exception):
    pass


class ManifestException(DockerFormatException):
    pass


class MalformedSchema1Manifest(DockerFormatException):
    pass


class InvalidSchema1Signature(ManifestException):
    """
    Raised when there is a failure verifying the signature of a signed Docker 2.1 Manifest.
    """
    pass


@add_metaclass(abc.ABCMeta)
class ManifestInterface(object):
    """ Defines the interface for the various manifests types supported. """

    @property
    @abc.abstractmethod
    def digest(self):
        """ The digest of the manifest, including type prefix. """
        pass

    @property
    @abc.abstractmethod
    def media_type(self):
        """ The media type of the schema. """
        pass

    @property
    @abc.abstractmethod
    def manifest_dict(self):
        """ Returns the manifest as a dictionary ready to be serialized to JSON. """
        pass

    @property
    @abc.abstractmethod
    def bytes(self):
        """ Returns the bytes of the manifest. """
        pass

    @property
    @abc.abstractmethod
    def layers(self):
        """ Returns the layers of this manifest, from base to leaf. """
        pass

    @property
    @abc.abstractmethod
    def leaf_layer_v1_image_id(self):
        """ Returns the Docker V1 image ID for the leaf (top) layer, if any, or None if none. """
        pass

    @property
    @abc.abstractmethod
    def legacy_image_ids(self):
        """ Returns the Docker V1 image IDs for the layers of this manifest or None if not applicable.
        """
        pass

    @property
    @abc.abstractmethod
    def blob_digests(self):
        """ Returns an iterator over all the blob digests referenced by this manifest,
                from base to leaf. The blob digests are strings with prefixes.
        """


"""
v1 implements pure data transformations according to the Docker Image Specification v1.1.

https://github.com/docker/docker/blob/master/image/spec/v1.1.md
"""


class DockerV1Metadata(namedtuple('DockerV1Metadata',
                                  ['namespace_name', 'repo_name', 'image_id', 'checksum',
                                   'content_checksum', 'created', 'comment', 'command',
                                   'parent_image_id', 'compat_json'])):
    """
  DockerV1Metadata represents all of the metadata for a given Docker v1 Image.
  The original form of the metadata is stored in the compat_json field.
  """


class Schema1Layer(namedtuple('Schema1Layer', ['digest', 'v1_metadata', 'raw_v1_metadata',
                                               'compressed_size'])):
    """
    Represents all of the data about an individual layer in a given Manifest.
    This is the union of the fsLayers (digest) and the history entries (v1_compatibility).
    """


class Schema1V1Metadata(namedtuple('Schema1V1Metadata', ['image_id', 'parent_image_id', 'created',
                                                         'comment', 'command', 'labels'])):
    """
    Represents the necessary data extracted from the v1 compatibility string in a given layer of a
    Manifest.
    """


class DockerSchema1Manifest(ManifestInterface):
    METASCHEMA = {
        'type': 'object',
        'properties': {
            DOCKER_SCHEMA1_SIGNATURES_KEY: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        DOCKER_SCHEMA1_PROTECTED_KEY: {
                            'type': 'string',
                        },
                        DOCKER_SCHEMA1_HEADER_KEY: {
                            'type': 'object',
                            'properties': {
                                'alg': {
                                    'type': 'string',
                                },
                                'jwk': {
                                    'type': 'object',
                                },
                            },
                            'required': ['alg', 'jwk'],
                        },
                        DOCKER_SCHEMA1_SIGNATURE_KEY: {
                            'type': 'string',
                        },
                    },
                    'required': [DOCKER_SCHEMA1_PROTECTED_KEY, DOCKER_SCHEMA1_HEADER_KEY,
                                 DOCKER_SCHEMA1_SIGNATURE_KEY],
                },
            },
            DOCKER_SCHEMA1_REPO_TAG_KEY: {
                'type': 'string',
            },
            DOCKER_SCHEMA1_REPO_NAME_KEY: {
                'type': 'string',
            },
            DOCKER_SCHEMA1_HISTORY_KEY: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        DOCKER_SCHEMA1_V1_COMPAT_KEY: {
                            'type': 'string',
                        },
                    },
                    'required': [DOCKER_SCHEMA1_V1_COMPAT_KEY],
                },
            },
            DOCKER_SCHEMA1_FS_LAYERS_KEY: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        DOCKER_SCHEMA1_BLOB_SUM_KEY: {
                            'type': 'string',
                        },
                    },
                    'required': [DOCKER_SCHEMA1_BLOB_SUM_KEY],
                },
            },
        },
        'required': [DOCKER_SCHEMA1_SIGNATURES_KEY, DOCKER_SCHEMA1_REPO_TAG_KEY,
                     DOCKER_SCHEMA1_REPO_NAME_KEY, DOCKER_SCHEMA1_FS_LAYERS_KEY,
                     DOCKER_SCHEMA1_HISTORY_KEY],
    }

    def __init__(self, manifest_bytes, validate=True):
        self._layers = None
        self._bytes = manifest_bytes

        try:
            self._parsed = json.loads(manifest_bytes)
        except ValueError as ve:
            raise MalformedSchema1Manifest('malformed manifest data: %s' % ve)

        try:
            validate_schema(self._parsed, DockerSchema1Manifest.METASCHEMA)
        except ValidationError as ve:
            raise MalformedSchema1Manifest('manifest data does not match schema: %s' % ve)

        self._signatures = self._parsed[DOCKER_SCHEMA1_SIGNATURES_KEY]
        self._tag = self._parsed[DOCKER_SCHEMA1_REPO_TAG_KEY]

        repo_name = self._parsed[DOCKER_SCHEMA1_REPO_NAME_KEY]
        repo_name_tuple = repo_name.split('/')
        if len(repo_name_tuple) > 1:
            self._namespace, self._repo_name = repo_name_tuple
        elif len(repo_name_tuple) == 1:
            self._namespace = ''
            self._repo_name = repo_name_tuple[0]
        else:
            raise MalformedSchema1Manifest('malformed repository name: %s' % repo_name)

        if validate:
            self._validate()

    @classmethod
    def for_latin1_bytes(cls, encoded_bytes, validate=True):
        return DockerSchema1Manifest(encoded_bytes.encode('utf-8'), validate)

    def _validate(self):
        for signature in self._signatures:
            bytes_to_verify = '{0}.{1}'.format(signature['protected'], b64encode(self._payload))
            signer = SIGNER_ALGS[signature['header']['alg']]
            key = keyrep(signature['header']['jwk'])
            gk = key.get_key()
            sig = b64decode(signature['signature'].encode('utf-8'))
            verified = signer.verify(bytes_to_verify, sig, gk)
            if not verified:
                raise InvalidSchema1Signature()

    @property
    def schema_version(self):
        return 1

    @property
    def content_type(self):
        return DOCKER_SCHEMA1_SIGNED_MANIFEST_CONTENT_TYPE

    @property
    def media_type(self):
        return DOCKER_SCHEMA1_SIGNED_MANIFEST_CONTENT_TYPE

    @property
    def signatures(self):
        return self._signatures

    @property
    def namespace(self):
        return self._namespace

    @property
    def repo_name(self):
        return self._repo_name

    @property
    def tag(self):
        return self._tag

    @property
    def json(self):
        return self._bytes

    @property
    def bytes(self):
        return self._bytes

    @property
    def manifest_json(self):
        return self._parsed

    @property
    def manifest_dict(self):
        return self._parsed

    @property
    def digest(self):
        return sha256_digest(self._payload)

    @property
    def image_ids(self):
        return {mdata.v1_metadata.image_id for mdata in self.layers}

    @property
    def legacy_image_ids(self):
        return {mdata.v1_metadata.image_id for mdata in self.layers}

    @property
    def parent_image_ids(self):
        return {mdata.v1_metadata.parent_image_id for mdata in self.layers
                if mdata.v1_metadata.parent_image_id}

    @property
    def checksums(self):
        return list({str(mdata.digest) for mdata in self.layers})

    @property
    def leaf_layer_v1_image_id(self):
        return self.layers[-1].v1_metadata.image_id

    @property
    def leaf_layer(self):
        return self.layers[-1]

    @property
    def created_datetime(self):
        created_datetime_str = self.leaf_layer.v1_metadata.created
        if created_datetime_str is None:
            return None

        try:
            return dateutil.parser.parse(created_datetime_str).replace(tzinfo=None)
        except:
            # parse raises different exceptions, so we cannot use a specific kind of handler here.
            return None

    @property
    def layers(self):
        if self._layers is None:
            self._layers = list(self._generate_layers())
        return self._layers

    @property
    def blob_digests(self):
        return [str(layer.digest) for layer in self.layers]

    def _generate_layers(self):
        """
        Returns a generator of objects that have the blobSum and v1Compatibility keys in them,
        starting from the base image and working toward the leaf node.
        """
        for blob_sum_obj, history_obj in reversed(
                zip(self._parsed[DOCKER_SCHEMA1_FS_LAYERS_KEY], self._parsed[DOCKER_SCHEMA1_HISTORY_KEY])):

            try:
                image_digest = Digest.parse_digest(blob_sum_obj[DOCKER_SCHEMA1_BLOB_SUM_KEY])
            except InvalidDigestException:
                raise MalformedSchema1Manifest(
                    'could not parse manifest digest: %s' % blob_sum_obj[DOCKER_SCHEMA1_BLOB_SUM_KEY])

            metadata_string = history_obj[DOCKER_SCHEMA1_V1_COMPAT_KEY]

            v1_metadata = json.loads(metadata_string)
            command_list = v1_metadata.get('container_config', {}).get('Cmd', None)
            command = json.dumps(command_list) if command_list else None

            # if not 'id' in v1_metadata:
            if 'id' not in v1_metadata:
                raise MalformedSchema1Manifest('id field missing from v1Compatibility JSON')

            labels = v1_metadata.get('config', {}).get('Labels', {}) or {}
            extracted = Schema1V1Metadata(v1_metadata['id'], v1_metadata.get('parent'), v1_metadata.get('created'),
                                          v1_metadata.get('comment'), command, labels)

            compressed_size = v1_metadata.get('Size')
            yield Schema1Layer(image_digest, extracted, metadata_string, compressed_size)

    @property
    def _payload(self):
        protected = str(self._signatures[0][DOCKER_SCHEMA1_PROTECTED_KEY])
        parsed_protected = json.loads(b64decode(protected))
        signed_content_head = self._bytes[:parsed_protected[DOCKER_SCHEMA1_FORMAT_LENGTH_KEY]]
        signed_content_tail = str(parsed_protected[DOCKER_SCHEMA1_FORMAT_TAIL_KEY])
        return signed_content_head + signed_content_tail

    def rewrite_invalid_image_ids(self, images_map):
        """
        Rewrites Docker v1 image IDs and returns a generator of DockerV1Metadata.

        If Docker gives us a layer with a v1 image ID that already points to existing
        content, but the checksums don't match, then we need to rewrite the image ID
        to something new in order to ensure consistency.
        """

        # Used to synthesize a new "content addressable" image id
        digest_history = hashlib.sha256()
        has_rewritten_ids = False
        updated_id_map = {}

        for layer in self.layers:
            digest_str = str(layer.digest)
            extracted_v1_metadata = layer.v1_metadata
            working_image_id = extracted_v1_metadata.image_id

            # Update our digest_history hash for the new layer data.
            digest_history.update(digest_str)
            digest_history.update("@")
            digest_history.update(layer.raw_v1_metadata.encode('utf-8'))
            digest_history.update("|")

            # Ensure that the v1 image's storage matches the V2 blob. If not, we've
            # found a data inconsistency and need to create a new layer ID for the V1
            # image, and all images that follow it in the ancestry chain.
            digest_mismatch = (extracted_v1_metadata.image_id in images_map and images_map[
                extracted_v1_metadata.image_id].content_checksum != digest_str)
            if digest_mismatch or has_rewritten_ids:
                working_image_id = digest_history.hexdigest()
                has_rewritten_ids = True

            # Store the new docker id in the map
            updated_id_map[extracted_v1_metadata.image_id] = working_image_id

            # Lookup the parent image for the layer, if any.
            parent_image_id = extracted_v1_metadata.parent_image_id
            if parent_image_id is not None:
                parent_image_id = updated_id_map.get(parent_image_id, parent_image_id)

            # Synthesize and store the v1 metadata in the db.
            v1_metadata_json = layer.raw_v1_metadata
            if has_rewritten_ids:
                v1_metadata_json = _updated_v1_metadata(v1_metadata_json, updated_id_map)

            updated_image = DockerV1Metadata(
                namespace_name=self.namespace,
                repo_name=self.repo_name,
                image_id=working_image_id,
                created=extracted_v1_metadata.created,
                comment=extracted_v1_metadata.comment,
                command=extracted_v1_metadata.command,
                compat_json=v1_metadata_json,
                parent_image_id=parent_image_id,
                checksum=None,  # TODO: Check if we need this.
                content_checksum=digest_str,
            )

            yield updated_image

###
# Digest utils (from file digest/digest_utils.py
###

# digest_tools constants


DIGEST_PATTERN = r'([A-Za-z0-9_+.-]+):([A-Fa-f0-9]+)'
REPLACE_WITH_PATH = re.compile(r'[+.]')
REPLACE_DOUBLE_SLASHES = re.compile(r'/+')


class InvalidDigestException(RuntimeError):
    pass


class Digest(object):
    DIGEST_REGEX = re.compile(DIGEST_PATTERN)

    def __init__(self, hash_alg, hash_bytes):
        self._hash_alg = hash_alg
        self._hash_bytes = hash_bytes

    def __str__(self):
        return '{0}:{1}'.format(self._hash_alg, self._hash_bytes)

    def __eq__(self, rhs):
        return isinstance(rhs, Digest) and str(self) == str(rhs)

    @staticmethod
    def parse_digest(digest):
        """ Returns the digest parsed out to its components. """
        match = Digest.DIGEST_REGEX.match(digest)
        if match is None or match.end() != len(digest):
            raise InvalidDigestException('Not a valid digest: %s', digest)

        return Digest(match.group(1), match.group(2))

    @property
    def hash_alg(self):
        return self._hash_alg

    @property
    def hash_bytes(self):
        return self._hash_bytes


def content_path(digest):
    """ Returns a relative path to the parsed digest. """
    parsed = Digest.parse_digest(digest)
    components = []

    # Generate a prefix which is always two characters, and which will be filled with leading zeros
    # if the input does not contain at least two characters. e.g. ABC -> AB, A -> 0A
    prefix = parsed.hash_bytes[0:2].zfill(2)
    pathish = REPLACE_WITH_PATH.sub('/', parsed.hash_alg)
    normalized = REPLACE_DOUBLE_SLASHES.sub('/', pathish).lstrip('/')
    components.extend([normalized, prefix, parsed.hash_bytes])
    return os.path.join(*components)


def sha256_digest(content):
    """ Returns a sha256 hash of the content bytes in digest form. """
    def single_chunk_generator():
        yield content
    return sha256_digest_from_generator(single_chunk_generator())


def sha256_digest_from_generator(content_generator):
    """ Reads all of the data from the iterator and creates a sha256 digest from the content
    """
    digest = hashlib.sha256()
    for chunk in content_generator:
        digest.update(chunk)
    return 'sha256:{0}'.format(digest.hexdigest())


def sha256_digest_from_hashlib(sha256_hash_obj):
    return 'sha256:{0}'.format(sha256_hash_obj.hexdigest())


def digests_equal(lhs_digest_string, rhs_digest_string):
    """ Parse and compare the two digests, returns True if the digests are equal, False otherwise.
    """
    return Digest.parse_digest(lhs_digest_string) == Digest.parse_digest(rhs_digest_string)
