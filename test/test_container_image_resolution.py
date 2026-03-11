"""
Tests for the image resolution logic in containers.run_container()
and containers._resolve_singularity_image().
We mock the framework-specific runners so no Docker/Apptainer install is needed.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings


def make_settings(**overrides):
    """Create a ProcessedContainerSettings with sensible defaults, then apply overrides.

    Accepts either ContainerFramework enum values or plain strings for 'framework';
    strings are resolved to their enum member so the property helpers work.
    """
    defaults = dict(
        framework=ContainerFramework.docker,
        unpack_singularity=False,
        base_url="docker.io",
        prefix="docker.io/reedcompbio",
        hash_length=7,
    )
    defaults.update(overrides)
    if isinstance(defaults["framework"], str):
        defaults["framework"] = ContainerFramework(defaults["framework"])
    return ProcessedContainerSettings(**defaults)


CONTAINER_SUFFIX = "pathlinker:v2"
DUMMY_COMMAND = ["echo", "test"]
DUMMY_VOLUMES = []
DUMMY_WORKDIR = "/workdir"
DUMMY_OUTDIR = "/output"


class TestRunContainerImageResolution:
    """Test the 5 branches of image resolution in run_container().

    Strategy: @patch replaces the real framework runner (run_container_docker /
    run_container_singularity) with a MagicMock for the duration of the test.
    The mock is injected as the last parameter of the test method (e.g. mock_docker).
    After calling run_container(), we inspect mock.call_args[0][0] to read the
    'container' string that run_container() resolved and passed to the runner —
    this is the value we want to assert on, without needing Docker or Apptainer.
    """

    @patch("spras.containers.run_container_docker", return_value="ok")
    def test_no_override_uses_default(self, mock_docker):
        """No image_override combines prefix/suffix using defaults."""
        settings = make_settings(framework="docker")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        # call_args[0] is the positional args tuple; [0] is the first arg (the container image string)
        container_arg = mock_docker.call_args[0][0]
        assert container_arg == "docker.io/reedcompbio/pathlinker:v2"

    @patch("spras.containers.run_container_docker", return_value="ok")
    def test_suffix_override_prepends_prefix(self, mock_docker):
        """Suffix-style override like 'pathlinker:v1234' --> prefix/override."""
        settings = make_settings(framework="docker", image_override="pathlinker:v1234")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        container_arg = mock_docker.call_args[0][0]
        assert container_arg == "docker.io/reedcompbio/pathlinker:v1234"

    @patch("spras.containers.run_container_docker", return_value="ok")
    def test_full_registry_override_used_as_is(self, mock_docker):
        """Full registry ref like 'ghcr.io/myorg/image:tag' --> used verbatim."""
        settings = make_settings(framework="docker", image_override="ghcr.io/myorg/pathlinker:v1234")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        container_arg = mock_docker.call_args[0][0]
        assert container_arg == "ghcr.io/myorg/pathlinker:v1234"

    @patch("spras.containers.run_container_docker", return_value="ok")
    def test_owner_image_override_prepends_base_url(self, mock_docker):
        """Owner/image override like 'someowner/oi2:latest' --> prepend base_url only."""
        settings = make_settings(framework="docker", image_override="someowner/oi2:latest")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        container_arg = mock_docker.call_args[0][0]
        assert container_arg == "docker.io/someowner/oi2:latest"

    @patch("spras.containers.run_container_docker", return_value="ok")
    def test_sif_override_with_docker_warns_and_falls_back(self, mock_docker):
        """.sif override + docker framework --> warning + fallback to default image."""
        settings = make_settings(framework="docker", image_override="images/pathlinker_v2.sif")
        from spras.containers import run_container

        with pytest.warns(UserWarning, match=r"\.sif file.*apptainer/singularity"):
            run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        container_arg = mock_docker.call_args[0][0]
        assert container_arg == "docker.io/reedcompbio/pathlinker:v2"

    @patch("spras.containers.run_container_singularity", return_value="ok")
    def test_sif_override_with_singularity_passes_through(self, mock_singularity):
        """.sif override + singularity --> container arg is still prefix/suffix (the .sif is
        resolved inside run_container_singularity via config.image_override)."""
        settings = make_settings(framework="singularity", image_override="images/pathlinker_v1234.sif")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        container_arg = mock_singularity.call_args[0][0]
        # The actual .sif is used inside run_container_singularity; run_container itself
        # passes the default container name and lets the inner function handle the override.
        assert container_arg == "docker.io/reedcompbio/pathlinker:v2"


class TestResolveSingularityImage:
    """Test _resolve_singularity_image(), the helper that determines which image
    apptainer/singularity should run.

    Cases 1 and 2 (unpack_singularity=False) need no mocks at all.
    Cases 3 and 4 (unpack_singularity=True) mock spython.main.Client so no
    real apptainer installation is required.
    """

    def test_no_override_no_unpack_returns_docker_uri(self):
        """Case 1: no override, no unpack --> 'docker://<container>'."""
        settings = make_settings(framework="singularity", unpack_singularity=False)
        from spras.containers import _resolve_singularity_image

        result = _resolve_singularity_image("docker.io/reedcompbio/pathlinker:v2", settings)
        assert result == "docker://docker.io/reedcompbio/pathlinker:v2"

    def test_local_sif_no_unpack_returns_sif_path(self):
        """Case 2: local .sif, no unpack --> returns the .sif path directly."""
        settings = make_settings(framework="singularity", unpack_singularity=False,
                                 image_override="images/pathlinker_v2.sif")
        from spras.containers import _resolve_singularity_image

        result = _resolve_singularity_image("docker.io/reedcompbio/pathlinker:v2", settings)
        assert result == "images/pathlinker_v2.sif"

    @patch("spython.main.Client")
    def test_local_sif_with_unpack_builds_sandbox(self, mock_client, tmp_path, monkeypatch):
        """Case 3: local .sif + unpack --> skips pull, calls Client.build, returns sandbox path."""
        # Run in tmp_path so the 'unpacked' directory is created there
        monkeypatch.chdir(tmp_path)

        settings = make_settings(framework="singularity", unpack_singularity=True,
                                 image_override="images/pathlinker_v2.sif")
        from spras.containers import _resolve_singularity_image

        result = _resolve_singularity_image("docker.io/reedcompbio/pathlinker:v2", settings)

        # Should NOT have called Client.pull (the .sif is already local)
        mock_client.pull.assert_not_called()
        # Should have called Client.build to unpack the .sif into a sandbox
        mock_client.build.assert_called_once()
        build_kwargs = mock_client.build.call_args
        assert build_kwargs[1]["recipe"] == "images/pathlinker_v2.sif"
        assert build_kwargs[1]["sandbox"] is True
        # Return value is the sandbox directory: unpacked/<stem of .sif>
        assert result == Path("unpacked") / "pathlinker_v2"

    @patch("spython.main.Client")
    def test_registry_with_unpack_pulls_and_builds(self, mock_client, tmp_path, monkeypatch):
        """Case 4: registry + unpack --> calls Client.pull then Client.build, returns sandbox path."""
        monkeypatch.chdir(tmp_path)
        mock_client.pull.return_value = str(tmp_path / "unpacked" / "pathlinker_v2.sif")

        settings = make_settings(framework="singularity", unpack_singularity=True)
        from spras.containers import _resolve_singularity_image

        result = _resolve_singularity_image("docker.io/reedcompbio/pathlinker:v2", settings)

        # Should have pulled the docker image
        mock_client.pull.assert_called_once()
        pull_args = mock_client.pull.call_args
        assert pull_args[0][0] == "docker://docker.io/reedcompbio/pathlinker:v2"
        # Should have unpacked into sandbox
        mock_client.build.assert_called_once()
        assert mock_client.build.call_args[1]["sandbox"] is True
        # Return value: unpacked/<image_tag> with colon replaced by underscore
        assert result == Path("unpacked") / "pathlinker_v2"

    @patch("spython.main.Client")
    def test_unpack_skips_build_if_sandbox_exists(self, mock_client, tmp_path, monkeypatch):
        """If the sandbox directory already exists (e.g. from a concurrent job), skip Client.build."""
        monkeypatch.chdir(tmp_path)
        # Pre-create the sandbox directory
        (tmp_path / "unpacked" / "pathlinker_v2").mkdir(parents=True)

        settings = make_settings(framework="singularity", unpack_singularity=True,
                                 image_override="images/pathlinker_v2.sif")
        from spras.containers import _resolve_singularity_image

        result = _resolve_singularity_image("docker.io/reedcompbio/pathlinker:v2", settings)

        mock_client.pull.assert_not_called()
        mock_client.build.assert_not_called()
        assert result == Path("unpacked") / "pathlinker_v2"
