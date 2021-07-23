from pathlib import PurePosixPath, PureWindowsPath
from src.util import prepare_path_docker, hash_params_sha1_base32


class TestUtil:
    def test_prepare_path_docker(self):
        assert prepare_path_docker(PureWindowsPath(r'D:\mydrive')) == r'//d/mydrive'
        assert prepare_path_docker(PureWindowsPath(r'Z:\network\users\me')) == r'//z/network/users/me'
        assert prepare_path_docker(PurePosixPath(r'/c/usr/me/')) == r'/c/usr/me'
        assert prepare_path_docker(PurePosixPath(r'/c/var/stuff')) == r'/c/var/stuff'

    def test_hash_params_sha1_base32(self):
        assert hash_params_sha1_base32({'k': 100}) == 'VQL7BDZOI6AG2NYBT7SOPGQ7IQ3SUS2V'
        assert hash_params_sha1_base32({'k': 1000}) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'
        assert hash_params_sha1_base32({'b': 0.3, 'w': 1.0, 'd': 10}) == 'P4OC5OSWG7L5QMREEIN7AX47XAGQZTAA'
        assert hash_params_sha1_base32({'d': 10, 'b': 0.3, 'w': 1.0}) == 'P4OC5OSWG7L5QMREEIN7AX47XAGQZTAA'
        assert hash_params_sha1_base32({'max_path_length': 3, 'local_search': 'Yes', 'rand_restarts': 10}) == 'GKEDDFZJEAKGZKGK7OTHNIGK4IEZKEFK'
