"""
Secrets and Licenses handler.
The results of these functions should never be printed.
"""

from pathlib import Path
from typing import Optional

import spras.config.config as config


def gurobi() -> Optional[Path]:
    """
    Gets the contents of the gurobi licenses, or None if not specified.
    """
    gurobi_str = config.config.secrets['gurobi']
    if not gurobi_str: return None
    
    gurobi_license = Path(gurobi_str)
    if not gurobi_license.exists(): return None

    return gurobi_license
