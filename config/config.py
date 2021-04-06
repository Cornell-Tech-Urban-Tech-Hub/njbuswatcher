import os

from config.common import config as default_config
from config.development import config as dev_config
from config.production import config as prod_config

environment = os.environ['PYTHON_ENV'] or 'development'
environment_config = None
if environment == 'development':
    environment_config = dev_config
if environment == 'production':
    environment_config = prod_config


config = {**environment_config, **default_config}
