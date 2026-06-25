#!/usr/bin/env python3
"""
Updates config/schema.json.
This should be done whenever a new algorithm is introduced,
or the config is otherwise directly changed.
"""

import json
from pathlib import Path

from spras.config.schema import RawConfig

current_path = Path(__file__).parent.resolve()

def main():
    config_schema = RawConfig.model_json_schema()
    (current_path / '..' / 'config' / 'schema.json').write_text(json.dumps(config_schema, indent=2))

if __name__ == "__main__":
    main()
