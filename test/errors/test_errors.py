import filecmp
from pathlib import Path
from spras.errors import ArtifactError, ArtifactSuccess, TimeoutArtifactError, mark_error, is_error, is_success, artifact_info_from_file, mark_success

OUTPUT_DIR = Path('test', 'errors', 'output')
EXPECTED_DIR = Path('test', 'errors', 'expected')

class TestErrors:
    def test_error(self):
        OUTPUT_DIR.mkdir(exist_ok=True)

        artifact_error = TimeoutArtifactError(duration=1)
        mark_error(OUTPUT_DIR / 'error.json', artifact_error)
        assert filecmp.cmp(EXPECTED_DIR / 'error.json', OUTPUT_DIR / 'error.json', shallow=True)
        assert is_error(OUTPUT_DIR / 'error.json')
        assert not is_success(OUTPUT_DIR / 'error.json')
        assert artifact_info_from_file(OUTPUT_DIR / 'error.json') == ArtifactError(details=artifact_error)

    def test_success(self):
        OUTPUT_DIR.mkdir(exist_ok=True)

        mark_success(OUTPUT_DIR / 'success.json')
        assert filecmp.cmp(EXPECTED_DIR / 'success.json', OUTPUT_DIR / 'success.json', shallow=True)
        assert is_success(OUTPUT_DIR / 'success.json')
        assert not is_error(OUTPUT_DIR / 'success.json')
        assert artifact_info_from_file(OUTPUT_DIR / 'success.json') == ArtifactSuccess()
