from importlib.resources import files
from pathlib import Path

import yaml

_path_config = str(files('camel').joinpath('config/config.yml'))

if not Path(_path_config).exists():
    raise FileNotFoundError(f'Config file not found: {_path_config}\nA sample file is available in {Path(_path_config).parent}')

with open(_path_config) as handle:
    config = yaml.load(handle, Loader=yaml.SafeLoader)
