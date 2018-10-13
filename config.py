import os
import configparser
import sys
from pathlib import Path


class Config:
    config = None
    _CFG_DEF_PATH = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'config.ini')
    _REQUIRED_FIELDS = [('Path', 'ProteinFolder', '/path/to/protein/folder'),
                        ('Tools', 'APBSPath', '/path/to/APBS/binary')]

    @staticmethod
    def get(section, option):
        if Config.config is None:
            Config.load_config(Config._CFG_DEF_PATH)
        return Config.config[section][option]

    @staticmethod
    def load_config(config_path):
        if not Path(config_path).exists():
            raise FileNotFoundError
        Config.config = configparser.ConfigParser()
        Config._set_default_fields()
        Config.config.read(config_path)
        Config._check_required_sections_fields()

    @staticmethod
    def save_default_config(config_path):
        Config.config = configparser.ConfigParser()
        Config._set_default_fields()
        Config._set_default_required()
        with open(config_path, 'w') as file:
            Config.config.write(file)

    @staticmethod
    def _check_required_sections_fields():
        errors = []
        for section, option, _ in Config._REQUIRED_FIELDS:
            try:
                Config.config.get(section, option)
            except configparser.NoSectionError:
                errors.append(('section', section))
            except configparser.NoOptionError:
                errors.append(('option', section, option))
        if errors:
            raise ConfigurationException(errors)

    @staticmethod
    def _set_default_fields():
        Config.config.read_dict({'Grid Parameters': dict(
            GridSize=65, GridSpacing=0.375, GridRadius=4.6875)})

    @staticmethod
    def _set_default_required():
        for section, option, default in Config._REQUIRED_FIELDS:
            if not Config.config.has_section(section):
                Config.config.add_section(section)
            Config.config.set(section, option, default)


class ConfigurationException(BaseException):

    def __init__(self, errors):
        self.value = f'Error while reading configuration file:\n'
        for typ, params in errors:
            if typ == 'section':
                self.value += 'Section {params} missing.\n'
            elif typ == 'option':
                self.value += 'Option {params[1]} in section {params[0]} missing.\n'

    def __str__(self):
        sys.stderr.print(self.value)
