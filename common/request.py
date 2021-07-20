import requests
from time import sleep
from logging import getLogger
from threading import Lock
from config import config


logger = getLogger(__name__)


def requests_get(**kwargs) -> requests.Response:
    return __requests_request(method='GET', **kwargs)


def requests_post(**kwargs) -> requests.Response:
    return __requests_request(method='POST', **kwargs)


def __requests_request(**kwargs) -> requests.Response:
    session = requests.Session()
    _lock = Lock()
    for _ in range(10):
        try:
            rp = session.request(timeout=10, proxies=config.proxy, **kwargs)
            if rp.status_code != 429:  # 429发生后大概5分钟左右结束限制
                if _lock.locked():
                    _lock.release()
                return rp
            else:
                if not _lock.locked():
                    _lock.acquire()
                logger.warning('Request failed! %d retry. Reason: Too Many Requests' % (_ + 1))
                sleep(30)
        except requests.exceptions.RequestException as e:
            if _lock.locked():
                _lock.release()
            logger.warning('Request failed! %d retry. Reason: %s' % (_ + 1, str(e)))
            sleep(1)
    if _lock.locked():
        _lock.release()
    logger.error("Request failed! Please check your network")
    raise requests.exceptions.RequestException

