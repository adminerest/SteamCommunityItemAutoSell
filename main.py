from price import Price, ItemCantSellException, CalculationFormulaWrongException
from steam.api import get_inventory
from common.variables import config
from item import retrieve_items, hash_descriptions
import logging
from steam.exceptions import *
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def start() -> None:
    assets, descriptions = get_inventory(config.steam_id, config.app_id, config.context_id,
                                         config.language, config.steam_login_secure)
    descriptions = hash_descriptions(descriptions)
    items = retrieve_items(assets, descriptions)
    del assets, descriptions
    total_sales = 0
    for item in items:
        if item.judge_can_sell():
            try:
                item.price = Price(item.appid, item.market_hash_name)
            except LoginCookieExpiredException:
                raise LoginCookieExpiredException
            except (ApiDoesntReturnSuccessException, RequestException,
                    UnknownSteamErrorException, ApiDoesntReturnNeededParameterException):
                continue
            try:
                item.price.calculate_price()
            except ItemCantSellException:
                logger.info(
                    "Item: %s, Asset ID: %s can't be sold Reason: orders not meet the config" %
                    (item.market_hash_name, item.assetid))
                continue
            except Exception:
                raise CalculationFormulaWrongException
            else:
                if item.judge_price_can_sell():
                    logger.info("Item: %s, Asset ID: %s, Sell Price: %f" % (item.market_hash_name,
                                                                            item.assetid,
                                                                            item.price.sell_price))
                    item.sell_on_market()
                    total_sales += 1
                else:
                    logger.info(
                        "Item: %s, Asset ID: %s can't be sold Reason: price not meet the config" %
                        (item.market_hash_name, item.assetid))
        else:
            logger.info(
                "Item: %s, Asset ID: %s can't be sold Reason: not allowed in config" % (item.market_hash_name,
                                                                                        item.assetid))
            # print(item.price.sell_price)
    logger.info("Total listed %d items" % total_sales)


if __name__ == '__main__':
    start()
