"""
The revision is an optional hash associated to all files in the designated output directory
to make sure that file _names_ are immutable. We attach the revision to three labels:

- Datasets
- Gold standards
- Algorithms

In the future, the spras revision may change depending on what files are effected (e.g specific algorithms
will have specific revisions that change as they get updated) to avoid unnecessary running in the
Reed-CompBio/spras-benchmarking repository.

This is an optional feature, as the `spras_revision` function below is dependent on a RECORD file
(described in the docstring associated with `spras_revision`.)

We provide the convenient attach_spras_revision used in ./config.py, and `detatch_spras_revision` used to get
rid of the revision for algorithms specifically.
"""

import functools
import hashlib
import importlib.metadata
from pathlib import Path
import sysconfig

@functools.cache
def spras_revision() -> str:
    """
    Gets the current revision of SPRAS.

    Note: This is not dependent on the SPRAS release version number nor the git commit, but rather solely on the PyPA RECORD file,
    (https://packaging.python.org/en/latest/specifications/recording-installed-packages/#the-record-file), which contains
    hashes of all of the installed SPRAS files [excluding RECORD itself], and is also included in the package distribution.
    This means that, when developing SPRAS, `spras_revision` will be updated when spras is initially installed. However, for editable
    pip installs (such as the pip installation used when developing spras), the `spras_revision` will not be updated.
    """
    try:
        site_packages_path = sysconfig.get_path("purelib") # where .dist-info is located.

        record_path = Path(
            site_packages_path,
            f"spras-{importlib.metadata.version('spras')}.dist-info",
            "RECORD"
        )
        with open(record_path, 'rb', buffering=0) as f:
            # Truncated to the magic value 8, the length of the short git revision.
            return hashlib.file_digest(f, 'sha256').hexdigest()[:8]
    except importlib.metadata.PackageNotFoundError as err:
        raise RuntimeError('spras is not an installed pip-module: did you forget to install SPRAS as a module?') from err


def attach_spras_revision(immutable_files: bool, label: str) -> str:
    """
    Attaches the SPRAS revision to a label.
    This function signature may become more complex as specific labels get versioned.

    @param label: The label to attach the SPRAS revision to.
    @param immutable_files: if False, this function is equivalent to `id`.
    """
    if immutable_files is False: return label
    # We use the `_` separator here instead of `-` as summary, analysis, and gold standard parts of the
    # Snakemake workflow process file names by splitting on hyphens to produce new jobs.
    # If this was separated with a hyphen, we would mess with that string manipulation logic.
    return f"{label}_{spras_revision()}"

def detatch_spras_revision(immutable_files: bool, attached_label: str) -> str:
    """The inverse of `attach_spras_revision`."""
    if immutable_files is False: return attached_label
    # `rpartition` starts at the end: detatch_spras_revision(b, attach_spras_revision(b, s)) = s for all b, s.
    return attached_label.rpartition("_")[0]
