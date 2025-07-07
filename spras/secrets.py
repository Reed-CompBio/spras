"""
Secrets and Licenses handler.
The results of these functions should never be printed.
"""

from pathlib import Path

import spras.config as config

def gurobi():
    """
    Gets the contents of the gurobi licenses, or None if not specified.
    """
    gurobi_license = Path(config.config.secrets.gurobi)
    if not gurobi_license.exists():
        return None
    return Path(config.config.secrets.gurobi).read_text()
