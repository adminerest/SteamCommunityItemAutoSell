from config import Config
from steam.api import get_wallet_fee_info
import logging
from logging import handlers
import os
import sys

time_handler_info = handlers.TimedRotatingFileHandler(filename=os.path.join(os.path.dirname(__file__),
                                                                            '../logs/info.log'),
                                                      when='D', backupCount=10)
time_handler_info.setLevel(logging.INFO)
log_format = '%(asctime)s - %(levelname)s Thread: %(threadName)s Message: %(message)s'
time_handler_info.setFormatter(logging.Formatter(log_format))


stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
log_format = '%(asctime)s - %(levelname)s Thread: %(threadName)s Message: %(message)s'
stream_handler.setFormatter(logging.Formatter(log_format))

logging.basicConfig(level=logging.NOTSET, handlers=(stream_handler, time_handler_info))

config = Config()


if config.debug:
    time_handler_debug = handlers.TimedRotatingFileHandler(filename=os.path.join(os.path.dirname(__file__),
                                                                                 '../logs/debug.log'),
                                                           when='D', backupCount=10)
    time_handler_debug.setLevel(logging.DEBUG)
    log_format = '%(asctime)s - %(levelname)s Thread: %(threadName)s Func: %(funcName)s-%(lineno)d: %(message)s'
    time_handler_debug.setFormatter(logging.Formatter(log_format))

    logging.root.addHandler(time_handler_debug)


logger = logging.getLogger(__name__)

logger.info('Success to load config file')

wallet = get_wallet_fee_info(config.steam_login_secure, config.steam_id)

logger.info("Success to get wallet info")
logger.debug("Wallet info: %s" % str(wallet.__dict__))
