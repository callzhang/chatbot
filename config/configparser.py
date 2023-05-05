'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-05-05 12:49:04
'''
import configparser


class ConfigParser:

    @staticmethod
    def get_mysql_config() -> str:
        return ConfigParser.get_config('mysql', 'mysql_connector')

    def get_config(self, section_name: str, item_name: str):
        config = self.init_config()
        # is configuration exist
        if config.has_option(section_name, item_name):
            # get info
            value = config.get(section_name, item_name)
            return value

    def get_all_config(self, section_name: str):
        _list = []

        config = self.init_config()
        for item in config.items(section_name):
            _list.append(item)

        return _list

    def init_config():
        config = configparser.ConfigParser()
        return config.read('config.ini')
