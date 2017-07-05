import logging

logger=None

def setup_logger():
    logger = logging.getLogger('root')
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.DEBUG)
    return logger


def log(*args, **kwargs):
    global logger
    if logger is None:
        logger=setup_logger()

    logtype = 'debug' if 'logtype' not in kwargs else kwargs['logtype']
    sep = ' ' if 'sep' not in kwargs else kwargs['sep']
    getattr(logger, logtype)(sep.join(str(a) for a in args))

