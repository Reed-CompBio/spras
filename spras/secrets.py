"""
Secrets and Licenses handler.
The results of these functions should never be printed.
"""

from pathlib import Path
from typing import Optional

import spras.config as config

# Parses an environment variable (format A=B)
# with optional comments
def parse_env(file: Path | str, comment_prefixes = ['#']) -> dict[str, str]:
    env_dict = dict()
    
    content = Path(file).read_text()
    for line in content.splitlines():
        if any(line.startswith(prefix) for prefix in comment_prefixes):
            continue

        # TODO: handle `=` escapes
        components = line.split("=")
        if len(components) != 2:
            raise RuntimeError(f"File {file} has malformed environment entries")
        
        key, value = components
        value = value.strip()
        key = key.strip()
        
        env_dict[key] = value
    
    return env_dict

def gurobi() -> Optional[dict[str, str]]:
    """
    Gets the contents of the gurobi licenses, or None if not specified.
    """
    gurobi_license = Path(config.config.secrets.gurobi)
    if not gurobi_license.exists():
        return None
    
    return parse_env(gurobi_license)
