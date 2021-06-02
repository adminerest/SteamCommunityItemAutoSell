from steam.api import get_item_price_graph, get_item_price_history, get_item_nameid
from datetime import timedelta, timezone
from typing import Dict
from common.variables import config, wallet
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Price(object):
    sell_price: float

    def __init__(self, appid: int, market_hash_name: str):
        """
        :param appid: the game's appid
        :param market_hash_name: The item market hash name
        :raises (LoginCookieExpiredException, ApiDoesntReturnSuccessException, RequestException,
                 UnknownSteamErrorException, ApiDoesntReturnNeededParameterException)
        """
        self.appid: int = appid
        self.market_hash_name: str = market_hash_name
        self.item_price_history = get_item_price_history(appid=appid,
                                                         market_hash_name=market_hash_name,
                                                         steam_login_secure=config.steam_login_secure)
        item_nameid: int = get_item_nameid(appid, market_hash_name)
        self.item_price_graph: Dict = get_item_price_graph(item_nameid,
                                                           wallet.currency,
                                                           config.language)

    def calculate_price(self) -> None:
        """
        Calculate the item's selling price

        :return: None
        :raises (CalculationFormulaWrongException, ItemCantSellException, Exception)
        """
        highest_buy_price = self.item_price_graph['highest_buy_order']
        lowest_sell_price = self.item_price_graph['lowest_sell_order']
        total_buy_orders = self.item_price_graph['buy_order_graph'][-1][1]
        total_sell_orders = self.item_price_graph['sell_order_graph'][-1][1]

        def get_history_sales_num(hours: int) -> int:
            if not isinstance(hours, (int, float)) or hours < 0 or hours > 999999:
                raise CalculationFormulaWrongException
            hours = int(hours)
            start = datetime.now(timezone.utc) - timedelta(hours=hours)
            sales_num = 0
            for i in range(len(self.item_price_history) - 1, -1, -1):
                if (start.timestamp() / 3600) <= (self.item_price_history[i][0].timestamp() / 3600):
                    sales_num += self.item_price_history[i][2]
                else:
                    break
            return sales_num

        def get_history_average_price(hours: int, weighted: bool = True) -> float:
            if not isinstance(hours, (int, float)) or not isinstance(weighted, bool) or hours < 0 or hours > 999999:
                raise CalculationFormulaWrongException
            hours = int(hours)
            total_price = 0.0
            weight = 0
            start = datetime.now(timezone.utc) - timedelta(hours=hours)
            for i in range(len(self.item_price_history) - 1, -1, -1):
                if (start.timestamp() / 3600) <= (self.item_price_history[i][0].timestamp() / 3600):
                    if weighted:
                        total_price += self.item_price_history[i][1] * self.item_price_history[i][2]
                        weight += self.item_price_history[i][2]
                    else:
                        total_price += self.item_price_history[i][1]
                        weight += 1
            return total_price / weight

        def get_history_highest_price(hours: int) -> float:
            if not isinstance(hours, (int, float)) or hours < 0 or hours > 999999:
                raise CalculationFormulaWrongException
            hours = int(hours)
            start = datetime.now(timezone.utc) - timedelta(hours=hours)
            highest_price = 0.0
            for i in range(len(self.item_price_history) - 1, -1, -1):
                if (start.timestamp() / 3600) <= (self.item_price_history[i][0].timestamp() / 3600):
                    highest_price = self.item_price_history[i][1] if self.item_price_history[i][1] > highest_price \
                        else highest_price
                else:
                    return highest_price
            return highest_price

        def sales_push_back(back_num: int) -> float:
            if not isinstance(back_num, (float, int)) or back_num < 0:
                raise CalculationFormulaWrongException
            back_num = int(back_num)
            for order in self.item_price_graph['sell_order_graph']:
                if order[1] >= back_num:
                    return order[0]
            return self.item_price_graph['sell_order_graph'][-1][0]

        history_sales_num = get_history_sales_num(config.price_setting['least_sells_hours'])
        logger.debug('history_sales_num: %d, total_buy_orders: %d, total_sell_orders: %d' % (history_sales_num,
                                                                                             total_buy_orders,
                                                                                             total_sell_orders))

        # Judge the item's market orders meet the config
        if history_sales_num < config.price_setting['hours_least_sells'] \
                or total_buy_orders < config.price_setting['least_buy_orders'] \
                or total_sell_orders < config.price_setting['least_sell_orders']:
            raise ItemCantSellException

        # Calculate the selling price
        self.sell_price = eval(config.price_setting['calculation_formula'])


class CalculationFormulaWrongException(Exception):
    """The calculation_formula is not right"""


class ItemCantSellException(Exception):
    """The item not meet the config setting"""

