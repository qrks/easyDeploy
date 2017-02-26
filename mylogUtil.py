# encoding=utf-8
import sys
import os
import logging
import logging.config
import time


logging.config.fileConfig("./logger.conf")
logger = logging.getLogger("logger01")

logger.debug('This is debug message')
logger.info('This is info message')
logger.warning('This is warning message')
