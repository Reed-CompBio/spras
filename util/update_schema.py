"""
Updates config/schema.json.
This should be done whenever a new algorithm is introduced,
or the config is otherwise directly changed.
"""

import json
from pathlib import Path

from spras.config.schema import RawConfig

config_schema = RawConfig.model_json_schema()
Path('config', 'schema.json').write_text(json.dumps(config_schema, indent=2))
