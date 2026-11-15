"""Tests for run_container_docker in spras.containers, with the Docker client mocked."""
import os
from pathlib import PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from spras.containers import run_container_docker


def _run_with_mock_client(tmp_path, run):
    """Call run_container_docker with a mocked Docker client whose containers.run is `run`."""
    client = MagicMock()
    client.containers.run.side_effect = run
    with patch("spras.containers.docker.from_env", return_value=client):
        out = run_container_docker("example/image:v1", ["echo", "hi"], [(tmp_path, PurePosixPath("/data"))], "/data")
    return out, client


def test_docker_output_is_decoded(tmp_path):
    out, _ = _run_with_mock_client(tmp_path, [b"hello\n"])
    assert out == "hello\n"


def test_docker_output_none(tmp_path):
    """A None output from docker-py is passed through instead of being decoded."""
    out, client = _run_with_mock_client(tmp_path, [None])
    assert out is None
    client.containers.run.assert_called_once()


@pytest.mark.skipif(not hasattr(os, "getuid"), reason="the owner reset only runs on Unix")
def test_docker_output_none_with_new_files(tmp_path):
    """The owner reset run still happens when the output is None."""
    def run(*args, **kwargs):
        (tmp_path / "new.txt").write_text("x")
        return None

    out, client = _run_with_mock_client(tmp_path, run)
    assert out is None
    assert client.containers.run.call_count == 2
