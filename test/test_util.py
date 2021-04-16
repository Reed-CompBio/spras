from pathlib import PurePosixPath, PureWindowsPath
from src.util import prepare_path_docker


class TestUtil:
    def test_prepare_path_docker(self):
        assert prepare_path_docker(PureWindowsPath(r'D:\mydrive')) == r'//d/mydrive'
        assert prepare_path_docker(PureWindowsPath(r'Z:\network\users\me')) == r'//z/network/users/me'
        assert prepare_path_docker(PurePosixPath(r'/c/usr/me/')) == r'/c/usr/me'
        assert prepare_path_docker(PurePosixPath(r'/c/var/stuff')) == r'/c/var/stuff'
