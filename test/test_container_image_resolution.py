"""
Tests for the image resolution logic in containers.run_container(),
containers.resolve_container_image(), and containers._prepare_singularity_image().
We mock the framework-specific runners so no Docker/Apptainer install is needed.
"""
import platform
import warnings
from pathlib import Path
from typing import NamedTuple, Optional
from unittest.mock import patch

import pytest

from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings
from spras.containers import ResolvedImage, resolve_container_image


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
    'container' string that run_container() resolved and passed to the runner --
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
    def test_sif_override_with_singularity_passes_sif(self, mock_singularity):
        """.sif override + singularity --> first arg is a ResolvedImage with the .sif path."""
        settings = make_settings(framework="singularity", image_override="images/pathlinker_v1234.sif")
        from spras.containers import run_container

        run_container(CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES, DUMMY_WORKDIR, DUMMY_OUTDIR, settings)
        resolved_arg = mock_singularity.call_args[0][0]
        assert isinstance(resolved_arg, ResolvedImage)
        assert resolved_arg.image == "images/pathlinker_v1234.sif"
        assert resolved_arg.is_local_sif is True


class _OverrideCase(NamedTuple):
    id: str
    settings_kw: dict
    expected_image: str
    expected_is_sif: bool
    warn_match: Optional[str]  # None means no warning should be raised


_OVERRIDE_CASES = [
    _OverrideCase(
        id="no_override_uses_default",
        settings_kw=dict(framework="docker"),
        expected_image="docker.io/reedcompbio/pathlinker:v2",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="suffix_override_prepends_prefix",
        settings_kw=dict(framework="docker", image_override="pathlinker:v1234"),
        expected_image="docker.io/reedcompbio/pathlinker:v1234",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="full_registry_override_used_as_is",
        settings_kw=dict(framework="docker", image_override="ghcr.io/myorg/pathlinker:v1234"),
        expected_image="ghcr.io/myorg/pathlinker:v1234",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="owner_image_override_prepends_base_url",
        settings_kw=dict(framework="docker", image_override="someowner/oi2:latest"),
        expected_image="docker.io/someowner/oi2:latest",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="sif_override_with_docker_warns_and_returns_default",
        settings_kw=dict(framework="docker", image_override="images/pathlinker_v2.sif"),
        expected_image="docker.io/reedcompbio/pathlinker:v2",
        expected_is_sif=False,
        warn_match=r"\.sif file.*apptainer/singularity"),
    _OverrideCase(
        id="sif_override_with_singularity_returns_sif",
        settings_kw=dict(framework="singularity", image_override="images/pathlinker_v1234.sif"),
        expected_image="images/pathlinker_v1234.sif",
        expected_is_sif=True,
        warn_match=None),
    _OverrideCase(
        id="excessive_path_depth_warns",
        settings_kw=dict(framework="docker", image_override="a/b/c/d/e/f"),
        expected_image="docker.io/a/b/c/d/e/f",
        expected_is_sif=False,
        warn_match="path components"),
    _OverrideCase(
        id="bare_hostname_warns",
        settings_kw=dict(framework="docker", image_override="hello.world"),
        expected_image="docker.io/reedcompbio/hello.world",
        expected_is_sif=False,
        warn_match="looks like a hostname"),
    _OverrideCase(
        id="valid_override_no_warning",
        settings_kw=dict(framework="docker", image_override="myimage:v2"),
        expected_image="docker.io/reedcompbio/myimage:v2",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="custom_registry_prefix",
        settings_kw=dict(framework="docker", base_url="ghcr.io", prefix="ghcr.io/myorg"),
        expected_image="ghcr.io/myorg/pathlinker:v2",
        expected_is_sif=False,
        warn_match=None),
    _OverrideCase(
        id="owner_image_with_custom_base_url",
        settings_kw=dict(framework="docker", base_url="ghcr.io", image_override="otherowner/img:v1"),
        expected_image="ghcr.io/otherowner/img:v1",
        expected_is_sif=False,
        warn_match=None),
]


class TestResolveContainerImage:
    """Direct unit tests for resolve_container_image()
    """

    @pytest.mark.parametrize(
        "settings_kw, expected_image, expected_is_sif, warn_match",
        [(c.settings_kw, c.expected_image, c.expected_is_sif, c.warn_match) for c in _OVERRIDE_CASES],
        ids=[c.id for c in _OVERRIDE_CASES],
    )
    def test_resolve(self, settings_kw, expected_image, expected_is_sif, warn_match):
        settings = make_settings(**settings_kw)
        if warn_match:
            with pytest.warns(UserWarning, match=warn_match):
                result = resolve_container_image(CONTAINER_SUFFIX, settings)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                result = resolve_container_image(CONTAINER_SUFFIX, settings)
        assert result.image == expected_image
        assert result.is_local_sif == expected_is_sif


class TestPrepareSingularityImage:
    """Test _prepare_singularity_image(), the helper that prepares the image
    that apptainer/singularity should run.

    Cases 3 and 4 (unpack_singularity=False) need no mocks at all.
    Cases 1 and 2 (unpack_singularity=True) mock spython.main.Client so no
    real apptainer installation is required.

    Case numbering matches _prepare_singularity_image's docstring:
      1. unpack + local .sif
      2. unpack + registry
      3. local .sif, no unpack
      4. registry, no unpack
    """

    @patch("spython.main.Client")
    def test_local_sif_with_unpack_builds_sandbox(self, mock_client, tmp_path, monkeypatch):
        """Case 1: local .sif + unpack --> skips pull, calls Client.build, returns sandbox path."""
        # Run in tmp_path so the 'unpacked' directory is created there
        monkeypatch.chdir(tmp_path)

        settings = make_settings(framework="singularity", unpack_singularity=True)
        from spras.containers import _prepare_singularity_image

        resolved = ResolvedImage(image="images/pathlinker_v2.sif", is_local_sif=True)
        result = _prepare_singularity_image(resolved, settings)

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
        """Case 2: registry + unpack --> calls Client.pull then Client.build, returns sandbox path."""
        monkeypatch.chdir(tmp_path)
        mock_client.pull.return_value = str(tmp_path / "unpacked" / "pathlinker_v2.sif")

        settings = make_settings(framework="singularity", unpack_singularity=True)
        from spras.containers import _prepare_singularity_image

        resolved = ResolvedImage(image="docker.io/reedcompbio/pathlinker:v2", is_local_sif=False)
        result = _prepare_singularity_image(resolved, settings)

        # Should have pulled the docker image
        mock_client.pull.assert_called_once()
        pull_args = mock_client.pull.call_args
        assert pull_args[0][0] == "docker://docker.io/reedcompbio/pathlinker:v2"
        # Should have unpacked into sandbox
        mock_client.build.assert_called_once()
        assert mock_client.build.call_args[1]["sandbox"] is True
        # Return value: unpacked/<image_tag> with colon replaced by underscore
        assert result == Path("unpacked") / "pathlinker_v2"

    def test_local_sif_no_unpack_returns_sif_path(self):
        """Case 3: local .sif, no unpack --> returns the .sif path directly."""
        settings = make_settings(framework="singularity", unpack_singularity=False)
        from spras.containers import _prepare_singularity_image

        resolved = ResolvedImage(image="images/pathlinker_v2.sif", is_local_sif=True)
        result = _prepare_singularity_image(resolved, settings)
        assert result == "images/pathlinker_v2.sif"

    def test_no_override_no_unpack_returns_docker_uri(self):
        """Case 4: registry image, no unpack --> 'docker://<image>'."""
        settings = make_settings(framework="singularity", unpack_singularity=False)
        from spras.containers import _prepare_singularity_image

        resolved = ResolvedImage(image="docker.io/reedcompbio/pathlinker:v2", is_local_sif=False)
        result = _prepare_singularity_image(resolved, settings)
        assert result == "docker://docker.io/reedcompbio/pathlinker:v2"

    @patch("spython.main.Client")
    def test_unpack_skips_build_if_sandbox_exists(self, mock_client, tmp_path, monkeypatch):
        """If the sandbox directory already exists (e.g. from a concurrent job), skip Client.build."""
        monkeypatch.chdir(tmp_path)
        # Pre-create the sandbox directory
        (tmp_path / "unpacked" / "pathlinker_v2").mkdir(parents=True)

        settings = make_settings(framework="singularity", unpack_singularity=True)
        from spras.containers import _prepare_singularity_image

        resolved = ResolvedImage(image="images/pathlinker_v2.sif", is_local_sif=True)
        result = _prepare_singularity_image(resolved, settings)

        mock_client.pull.assert_not_called()
        mock_client.build.assert_not_called()
        assert result == Path("unpacked") / "pathlinker_v2"


@pytest.mark.skipif(platform.system() != 'Linux', reason="run_container_singularity is Linux-only")
class TestSifOverrideReachesClientExecute:
    """Integration test: verify that a .sif override set on container_settings
    flows all the way from run_container() through run_container_singularity()
    and _prepare_singularity_image() down to Client.execute(image=<the .sif>).

    Only spython.main.Client is mocked -- all intermediate layers run for real.
    Skipped on non-Linux because run_container_singularity raises NotImplementedError there.
    """

    @patch("spython.main.Client")
    def test_sif_override_reaches_client_execute(self, mock_client):
        from spras.containers import run_container

        settings = make_settings(
            framework="singularity",
            unpack_singularity=False,
            image_override="images/pathlinker_v2.sif",
        )

        run_container(
            CONTAINER_SUFFIX, DUMMY_COMMAND, DUMMY_VOLUMES,
            DUMMY_WORKDIR, DUMMY_OUTDIR, settings,
        )

        mock_client.execute.assert_called_once()
        assert mock_client.execute.call_args[1]["image"] == "images/pathlinker_v2.sif"


class TestEndToEndOverride:
    """Test that image overrides set via containers.images in the config actually
    flow through runner.run() --> algorithm.run() with the correct image_override
    on the container_settings object.

    We mock PathLinker.run (the algorithm entry point) to avoid file I/O and
    container execution, and inspect the container_settings it receives.
    """

    @patch("spras.pathlinker.PathLinker.run")
    def test_sif_override_flows_through_runner(self, mock_run):
        """runner.run() should set image_override from settings.images before calling the algorithm."""
        from spras.runner import run as runner_run

        settings = make_settings(
            framework="singularity",
            images={"pathlinker": "my_algorithm.sif"},
        )

        runner_run(
            "pathlinker",
            {"nodetypes": "dummy_nodes.txt", "network": "dummy_edges.txt"},
            "output.txt",
            {"k": 5},
            settings,
        )

        mock_run.assert_called_once()
        # container_settings is the 4th positional arg: run(inputs, output_file, args, container_settings)
        call_settings = mock_run.call_args[0][3]
        assert call_settings.image_override == "my_algorithm.sif"

    @patch("spras.pathlinker.PathLinker.run")
    def test_no_override_leaves_image_override_none(self, mock_run):
        """When no image override is configured, image_override should remain None."""
        from spras.runner import run as runner_run

        settings = make_settings(framework="docker")

        runner_run(
            "pathlinker",
            {"nodetypes": "dummy_nodes.txt", "network": "dummy_edges.txt"},
            "output.txt",
            {"k": 5},
            settings,
        )

        mock_run.assert_called_once()
        # container_settings is the 4th positional arg: run(inputs, output_file, args, container_settings)
        call_settings = mock_run.call_args[0][3]
        assert call_settings.image_override is None
