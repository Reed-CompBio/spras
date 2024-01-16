from pathlib import PurePosixPath, PureWindowsPath

import pytest

import spras.config as config
from spras.containers import convert_docker_path, prepare_path_docker, prepare_volume
from spras.util import hash_params_sha1_base32

config.init_from_file("config/config.yaml")

class TestUtil:
    def test_prepare_path_docker(self):
        assert prepare_path_docker(PureWindowsPath(r'D:\mydrive')) == r'//d/mydrive'
        assert prepare_path_docker(PureWindowsPath(r'Z:\network\users\me')) == r'//z/network/users/me'
        assert prepare_path_docker(PurePosixPath(r'/c/usr/me/')) == r'/c/usr/me'
        assert prepare_path_docker(PurePosixPath(r'/c/var/stuff')) == r'/c/var/stuff'

    def test_hash_params_sha1_base32(self):
        # Tests without length argument
        assert hash_params_sha1_base32({'k': 100}) == 'VQL7BDZOI6AG2NYBT7SOPGQ7IQ3SUS2V'
        assert hash_params_sha1_base32({'k': 1000}) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'
        assert hash_params_sha1_base32({'b': 0.3, 'w': 1.0, 'd': 10}) == 'P4OC5OSWG7L5QMREEIN7AX47XAGQZTAA'
        assert hash_params_sha1_base32({'d': 10, 'b': 0.3, 'w': 1.0}) == 'P4OC5OSWG7L5QMREEIN7AX47XAGQZTAA'
        assert hash_params_sha1_base32({'max_path_length': 3, 'local_search': 'Yes', 'rand_restarts': 10}) == 'GKEDDFZJEAKGZKGK7OTHNIGK4IEZKEFK'

        # Tests with length argument
        assert hash_params_sha1_base32({'k': 1000}, 7) == 'TFORORH'
        assert hash_params_sha1_base32({'k': 1000}, 1) == 'T'
        assert hash_params_sha1_base32({'k': 1000}, 0) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'
        assert hash_params_sha1_base32({'k': 1000}, -1) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'
        assert hash_params_sha1_base32({'k': 1000}, 1000) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'
        assert hash_params_sha1_base32({'k': 1000}, None) == 'TFORORHE4JUNRSI7QPHCXUUES4DLD6P4'

    # Cannot test the returned src dest mapping as easily because it is an absolute path
    # prepare_volume uses util.hash_filename so this serves as a test case for that function as well
    @pytest.mark.parametrize('filename, volume_base, expected_filename',
                             [('oi1-edges.txt', '/spras', '/spras/MG4YPNK/oi1-edges.txt'),
                              ('test/OmicsIntegrator1/input/oi1-edges.txt', '/spras', '/spras/ZNNT3GR/oi1-edges.txt'),
                              ('test/OmicsIntegrator1/output/', '/spras', '/spras/DPCSFJV/output'),
                              (PurePosixPath('test/OmicsIntegrator1/output/'), '/spras', '/spras/TNDO5TR/output'),
                              ('test/OmicsIntegrator1/output', PurePosixPath('/spras'), '/spras/TNDO5TR/output'),
                              ('../src', '/spras', '/spras/NNBVZ6X/src')])
    def test_prepare_volume(self, filename, volume_base, expected_filename):
        _, container_filename = prepare_volume(filename, volume_base)
        assert container_filename == expected_filename

    def test_convert_docker_path(self):
        src_path = PureWindowsPath(r'C:/Users/admin/spras/test/OmicsIntegrator1/output/')
        dest_path = PurePosixPath('/spras/FQAXPPD/output')
        file_path = PureWindowsPath(r'C:/Users/admin/spras/test/OmicsIntegrator1/output/oi1_dummyForest.sif')
        expected_path = PurePosixPath('/spras/FQAXPPD/output/oi1_dummyForest.sif')
        assert convert_docker_path(src_path, dest_path, file_path) == expected_path

        src_path = PurePosixPath('/c/usr/me')
        dest_path = PurePosixPath('/spras/FQAXPPD/output')
        file_path = PurePosixPath('/c/usr/me/oi1_dummyForest.sif')
        expected_path = PurePosixPath('/spras/FQAXPPD/output/oi1_dummyForest.sif')
        assert convert_docker_path(src_path, dest_path, file_path) == expected_path
