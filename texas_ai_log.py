import logging
# import settings
import os
import time 


ROOT_PATH = "./"
LOG_DIR = os.path.join(ROOT_PATH, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


class Log(object):

    @staticmethod
    def get_logger(name='main'):

        LOG_NAME = time.strftime("%Y%m%d%H%M%S", time.localtime())

        # create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        log_path = os.path.join(LOG_DIR, LOG_NAME)
        # create console handler and set level to debug
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(message)s')

        # add formatter to file_handler
        file_handler.setFormatter(formatter)

        # add file_handler to logger
        logger.addHandler(file_handler)

        return logger


logger = Log.get_logger() 