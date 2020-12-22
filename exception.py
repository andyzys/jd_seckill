#!/usr/bin/env python
# -*- encoding=utf8 -*-
from jd_logger import logger


class SKException(Exception):

    def __init__(self, message):
        super().__init__(message)
        logger.error(message)
