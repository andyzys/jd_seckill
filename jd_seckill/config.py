#!/usr/bin/env python
# -*- encoding=utf8 -*-

import os
import configparser


class EnvInterpolation(configparser.BasicInterpolation):
    """
    尝试从系统环境变量中读取，如果读取失败，则直接使用配置值
    """

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        # 无法获取则返回原值
        return os.path.expandvars(value)


class Config(object):
    def __init__(self, config_file='config.ini'):
        self._path = os.path.join(os.getcwd(), config_file)
        if not os.path.exists(self._path):
            raise FileNotFoundError("No such file: config.ini")
        self._config = configparser.ConfigParser(interpolation=EnvInterpolation())
        self._config.read(self._path, encoding='utf-8-sig')
        self._configRaw = configparser.RawConfigParser(interpolation=EnvInterpolation())
        self._configRaw.read(self._path, encoding='utf-8-sig')

    def get(self, section, name):
        return self._config.get(section, name)

    def getRaw(self, section, name):
        return self._configRaw.get(section, name)


global_config = Config()
