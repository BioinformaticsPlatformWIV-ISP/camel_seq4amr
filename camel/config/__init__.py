import pkg_resources
import yaml

_path_config = pkg_resources.resource_filename('camel', 'config/config.yml')

with open(_path_config) as handle:
    config = yaml.load(handle, Loader=yaml.SafeLoader)
