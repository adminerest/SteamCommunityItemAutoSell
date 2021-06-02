from typing import List, Dict
from steam.api import sell_item_on_market
from price import Price
from steam.exceptions import *
from common.variables import config, wallet
import logging

logger = logging.getLogger(__name__)


class Item(object):
    price: Price

    def __init__(self, appid: int, contextid: str, assetid: str, classid: str, instanceid: str, amount: str,
                 tradable: int, marketable: int, name: str, type_detail: str, tags: List[Dict],
                 publisher_fee: float = None,
                 market_name: str = None, market_hash_name: str = None):
        """
        The item class

        :param appid: the game's appid
        :param contextid: the item's contextid
        :param assetid: the item's assetid
        :param classid: the item's classid
        :param instanceid: the item's instanceid
        :param amount: the item's amount
        :param tradable: the item is tradable or not
        :param marketable: the item is marketable or not
        :param name:
        :param type_detail: The item type detail
        :param tags: The item's tags
        :param publisher_fee: The item's publisher fee
        :param market_name: The item's market name
        :param market_hash_name: The item market hash name
        :raises (ApiDoesntReturnNeededParameterException, UnknownSteamErrorException)
        """
        # TODO: 正常情况下物品的发行商费率放在descriptions里，如果没有则按照默认10%计算
        self.appid: int = appid
        self.contextid: str = contextid
        self.assetid: str = assetid
        self.classid: str = classid
        self.instanceid: str = instanceid
        self.amount: str = amount
        self.tradable: bool = False if tradable == 0 else True
        self.name: str = name
        self.type_detail: str = type_detail
        self.market_name: str = market_name
        self.market_hash_name: str = market_hash_name
        self.marketable: bool = False if marketable == 0 else True
        self.publisher_fee: float = publisher_fee
        try:
            self.category: Dict = {tag['category']: tag for tag in tags}
        except KeyError as e:
            logger.error('Item: %s, Asset ID: %s; The item category info is not correct' % (self.market_hash_name,
                                                                                            self.assetid))
            logger.debug(tags)
            raise ApiDoesntReturnNeededParameterException('The item category info is not correct')

        # Convert item_class to num
        if self.category['item_class']['internal_name'] == 'item_class_2':
            if self.category['cardborder']['internal_name'] == 'cardborder_0':
                self.type1 = 20
            elif self.category['cardborder']['internal_name'] == 'cardborder_1':
                self.type1 = 21
            else:
                logger.error(
                    'Item: %s, Asset ID: %s; Unknown Card Border' % (self.market_hash_name, self.assetid))
                logger.debug("Card Border: %s" % self.category['cardborder']['internal_name'])
                raise UnknownSteamErrorException('Unknown Card Border')
        else:
            self.type1 = int(self.category['item_class']['internal_name'].split('_')[-1])

    def judge_can_sell(self) -> bool:
        """
        Judge the item's type meets the config

        :return: Can sell = True
        """
        logger.debug('marketable: %s, type1: %d, type_detail: %s' % (self.marketable, self.type1, self.type_detail))
        return True if self.marketable and \
                       ((not config.allow_to_sell_item['enable'] or
                         (config.allow_to_sell_item['enable'] and
                          self.type1 in config.allow_to_sell_item['item_type'])) and
                        (not config.disallow_to_sell_item['enable'] or (config.disallow_to_sell_item['enable'] and
                                                                        self.type1 not in
                                                                        config.disallow_to_sell_item['item_type'])) and
                        (not config.allow_to_sell_item_detail['enable'] or (
                                config.allow_to_sell_item_detail['enable'] and
                                self.type_detail in config.allow_to_sell_item_detail['item_detail_type'])) and
                        (not config.disallow_to_sell_item_detail['enable'] or (
                                config.disallow_to_sell_item_detail['enable'] and
                                self.type_detail not in config.disallow_to_sell_item_detail[
                                    'item_detail_type']))) else False

    def judge_price_can_sell(self) -> bool:
        """
        Judge the item's selling price meet the price config

        :return: Can sell = True
        """
        if (config.price_setting['lowest_price'] is not None and
            self.price.sell_price < config.price_setting['lowest_price']) or \
                (config.price_setting['highest_price'] is not None and
                 self.price.sell_price > config.price_setting['highest_price']):
            return False
        if self.category['item_class']['internal_name'] == 'item_class_2':
            if self.category['cardborder']['internal_name'] == 'cardborder_0':
                if (config.price_setting['normal_card']['lowest_price'] is not None and
                    self.price.sell_price < config.price_setting['lowest_price']) or \
                        (config.price_setting['normal_card']['highest_price'] is not None and
                         self.price.sell_price > config.price_setting['highest_price']):
                    return False
            if self.category['cardborder']['internal_name'] == 'cardborder_1':
                if (config.price_setting['foil_card']['lowest_price'] is not None and
                    self.price.sell_price < config.price_setting['lowest_price']) or \
                        (config.price_setting['foil_card']['highest_price'] is not None and
                         self.price.sell_price > config.price_setting['highest_price']):
                    return False
        else:
            if (config.price_setting['other_item']['lowest_price'] is not None and
                self.price.sell_price < config.price_setting['lowest_price']) or \
                    (config.price_setting['other_item']['highest_price'] is not None and
                     self.price.sell_price > config.price_setting['highest_price']):
                return False
        return True

    def sell_on_market(self) -> None:
        """
        List the item on the steam market

        :raises (UnknownSteamErrorException, RequestException, ApiDoesntReturnSuccessException)
        """

        # Calculate the steam market fee
        fee = wallet.calculate_fee(self.price.sell_price, self.publisher_fee)
        sell_price_without_fee = int(self.price.sell_price * 100 - fee)
        logger.info('Item: %s, Asset ID: %s, Item sell price: %f, Item fee: %f, Sell price without fee: %f' % (
            self.market_hash_name, self.assetid, self.price.sell_price, fee / 100, sell_price_without_fee / 100))
        logger.info('Item: %s, Asset ID: %s starts to list on market' % (self.market_hash_name, self.assetid))
        result = sell_item_on_market(config.steam_login_secure, config.steam_id, self.appid, self.contextid,
                                     self.assetid, self.amount, sell_price_without_fee, config.language)
        if result['success']:
            logger.info('Item: %s list on market successfully. Asset ID: %s' % (self.market_hash_name,
                                                                                self.assetid))
            if result['requires_confirmation'] == 1:
                if result['needs_mobile_confirmation']:
                    logger.info('Item: %s, Asset ID: %s needs mobile confirmation' % (self.market_hash_name,
                                                                                      self.assetid))
                elif result['needs_email_confirmation']:
                    logger.info('Item: %s, Asset ID: %s needs email confirmation' % (self.market_hash_name,
                                                                                     self.assetid))
        else:
            logger.warning('Failed to list Item: %s. Asset ID: %s on market; Reason: %s' % (self.market_hash_name,
                                                                                            self.assetid,
                                                                                            result.get('message',
                                                                                                       '')))
            logger.debug(result)


def retrieve_items(assets: List[Dict], descriptions: Dict[int, Dict[str, Dict[str, Dict]]]) -> List[Item]:
    """
    Combine assets and descriptions to Item

    :param assets: Assets obtained from the Inventory API
    :param descriptions: Descriptions from function: ``hash_descriptions``
    :return: List contains :class:`Item <Item>` object
    """
    items = []
    for asset in assets:
        description = descriptions[asset['appid']][asset['classid']][asset['instanceid']]
        try:
            items.append(Item(
                appid=description['appid'],
                contextid=asset['contextid'],
                assetid=asset['assetid'],
                classid=description['classid'],
                instanceid=description['instanceid'],
                amount=asset['amount'],
                tradable=description['tradable'],
                name=description['name'],
                type_detail=description['type'],
                market_name=description['market_name'],
                market_hash_name=description['market_hash_name'],
                marketable=description['marketable'],
                tags=description['tags'],
                publisher_fee=description.get('publisher_fee', None)
            ))
        except (ApiDoesntReturnNeededParameterException, UnknownSteamErrorException):
            pass
    logger.info('Get %d items in total' % len(items))
    return items


def hash_descriptions(descriptions: List[Dict]) -> Dict[int, Dict[str, Dict[str, Dict]]]:
    """
    Make a hash table for descriptions

    :param descriptions: Descriptions obtained from the Inventory API
    :return: {'appid': {'classid': {'instanceid': Dict[full_description]}}}
    """
    descriptions_old = descriptions
    descriptions = {}
    for description in descriptions_old:
        try:
            descriptions.setdefault(description['appid'], {}).setdefault(description['classid'],
                                                                         {})[description['instanceid']] = description
        except KeyError:
            logger.error("Get unknown/wrong parameter when hashing descriptions")
            logger.debug(description)
            raise ApiDoesntReturnNeededParameterException('Get unknown/wrong parameter when hashing descriptions')
    return descriptions
