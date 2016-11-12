import logging

def getLogger(name, level=logging.NOTSET):
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s:%(threadName)s:%(pathname)s:%(funcName)s:%(lineno)d - %(message)s')
    ch.setFormatter(formatter)
    LOGGER = logging.getLogger(name)
    LOGGER.setLevel(level)
    LOGGER.addHandler(ch)

    return LOGGER
