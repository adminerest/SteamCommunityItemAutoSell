import re
from typing import List, Dict
from common.request import requests_get, requests_post
from json import loads, JSONDecodeError
from steam.exceptions import *
from common.common import parse_datetime
from wallet import Wallet
import logging
from urllib.parse import quote


logger = logging.getLogger(__name__)


def get_inventory(steam_id: str, app_id: int, context_id: str, language: str, steam_login_secure: str = None,
                  assets: List[Dict] = None, descriptions: List[Dict] = None) -> (List[Dict], List[Dict]):
    """
    Get user's game (Steam) inventory info and return items' info and descriptions

    :param steam_id: The steam id you want to get the inventory
    :param app_id: The app's id you want to get the inventory
    :param context_id: The in-app inventory category id you want to get the inventory
    :param language: Preferred language
    :param steam_login_secure: The cookie of the browser that has logged in to the steam account
    :param assets: Assets from this function
    :param descriptions: Descriptions from this function
    :return: (assets[], descriptions[])
    :raises (InventoryPrivateException, ApiDoesntReturnSuccessException, ApiDoesntReturnNeededParameterException,
             RequestException, UnknownSteamErrorException)
    """

    last_asset_id = None
    if assets is None:
        assets = []
    if descriptions is None:
        descriptions = []
    while True:
        url = 'https://steamcommunity.com/inventory/%s/%d/%s' % (steam_id, app_id, context_id)
        params = {
            'l': language,
            'count': 5000,
            'start_assetid': last_asset_id
        }
        cookies = {
            'steamLoginSecure': steam_login_secure
        }
        rp = requests_get(url=url, cookies=cookies, params=params)
        if rp.status_code == 403:  # When the user's inventory is private
            logger.error("User: %s inventory is private" % steam_id)
            raise InventoryPrivateException("the user's inventory you request is private.")
        try:
            data = loads(rp.text)  # TODO: vpn断开连接时可能导致数据传输不完整
        except JSONDecodeError:
            logger.error("The steam didn't response right content when get_inventory")
            logger.debug(rp.content)
            raise UnknownSteamErrorException("The steam didn't response right content")
        if not data or data.get('success', 0) != 1:  # Error when steam getting inventory
            logger.error("The get_inventory API doesn't return a right response.")
            logger.debug(data)
            raise ApiDoesntReturnSuccessException("The get_inventory API doesn't return a right response.")
        assets += data.get('assets', [])
        descriptions += data.get('descriptions', [])
        if not data.get('more_items', False):  # If the total number of items is less than 5000
            logger.info('Success to get user: %s inventory' % steam_id)
            logger.debug('assets length: %d' % len(assets))
            return assets, descriptions
        try:
            last_asset_id = data.get('last_assetid')
        except KeyError:
            # When the api doesn't response the last item's asset id
            logger.error("The get_inventory API doesn't give last_assetid when returning more_items.")
            logger.debug(data)
            raise ApiDoesntReturnNeededParameterException("The get_inventory API doesn't give "
                                                          "last_assetid when returning more_items.")


def get_item_price_history(appid: int, market_hash_name: str, steam_login_secure: str) -> List[List]:
    """
    Get item history sales

    :param appid: The app's id which the item belows to
    :param market_hash_name: The value of the item's market_hash_name
    :param steam_login_secure: The cookie of the browser that has logged in to the steam account
    :return: The list of the item's history price. Format: List[List[time, sell_price, sell_amount]]
    :rtype List[List[datetime, float, int]]
    :raises (LoginCookieExpiredException, ApiDoesntReturnSuccessException, RequestException, UnknownSteamErrorException,
             ApiDoesntReturnNeededParameterException)
    """
    url = 'https://steamcommunity.com/market/pricehistory/'
    params = {
        'appid': appid,
        'market_hash_name': market_hash_name,
    }
    cookies = {
        'steamLoginSecure': steam_login_secure
    }
    rp = requests_get(url=url, cookies=cookies, params=params)
    if rp.status_code == 400:  # When steam_login_secure is wrong
        logger.error("The steam cookie is expired")
        raise LoginCookieExpiredException
    try:
        data = loads(rp.text)  # TODO: vpn断开连接时可能导致数据传输不完整
    except JSONDecodeError:
        logger.error("The steam didn't response right content when get_item_price_history")
        logger.debug(rp.content)
        raise UnknownSteamErrorException("The steam didn't response right content")
    if not data or not data.get('success', False):  # Error when steam getting price history
        logger.error("The get_item_price_history API doesn't return a right response.")
        logger.debug(data)
        raise ApiDoesntReturnSuccessException("The get_item_price_history API doesn't return a right response.")
    try:
        prices = data['prices']
    except KeyError:
        # The API's response doesn't contain history price info
        logger.error("The get_item_price_history API doesn't return history price info")
        logger.debug(data)
        raise ApiDoesntReturnNeededParameterException("The get_item_price_history API doesn't"
                                                      " return history price info")
    count = 0
    for price in prices:
        try:
            price[0] = parse_datetime(price[0])
            price[2] = int(price[2])
        except (IndexError, KeyError, ValueError):
            count += 1
            if count > 10 or len(price) < 200:
                # If there are too much error data when parsing history price info then raise an exception
                logger.error("The get_item_price_history API returns too many errors")
                logger.debug(data)
                raise ApiDoesntReturnNeededParameterException("The get_item_price_history API returns too many errors")
            else:
                pass
    logger.debug("Success to get item's price history")
    return prices


def get_wallet_fee_info(steam_login_secure: str, steam_id: str) -> Wallet:
    """
    Get steam wallet fee information

    :param steam_login_secure: The cookie of the browser that has logged in to the steam account
    :param steam_id: The steam id you want to use
    :return: :class:`Wallet`
    :raises (LoginCookieExpiredException, RequestException, UnknownSteamErrorException)
    """
    url = 'https://steamcommunity.com/profiles/%s/inventory/' % steam_id
    cookies = {
        'steamLoginSecure': steam_login_secure,
    }
    rp = requests_get(url=url, cookies=cookies)
    if rp.status_code != 200:
        logger.error("Error when getting wallet fee info")
        logger.debug(rp.content)
        raise UnknownSteamErrorException("Error when getting wallet fee info")
    try:
        wallet_info = loads(re.search(r'var g_rgWalletInfo = {.*}', rp.text, re.ASCII)[0].split('=')[1])
    except IndexError:
        logger.error("Didn't get the right wallet info. Maybe cookie expired")
        logger.debug(rp.text)
        raise UnknownSteamErrorException("Didn't get the right wallet info. Maybe cookie expired")
    if not wallet_info.get('success', False):  # If the cookie is expired, steam will return false in 'success'
        logger.error("The steam cookie is expired")
        logger.debug(wallet_info)
        raise LoginCookieExpiredException
    try:
        logger.debug("Success to get wallet_info")
        return Wallet(int(wallet_info.get('wallet_fee_base', 0)), float(wallet_info.get('wallet_fee_percent', 0.05),),
                      int(wallet_info.get('wallet_fee_minimum', 1)), wallet_info.get('wallet_currency'),
                      float(wallet_info.get('wallet_publisher_fee_percent_default', 0.1)))
    except ValueError:
        logger.error("Didn't get the right wallet info.")
        logger.debug(wallet_info)
        raise UnknownSteamErrorException("Didn't get the right wallet info.")


def get_item_nameid(appid: int, market_hash_name: str) -> int:
    """
    Get the item's item_nameid which is needed in function ``get_item_price_graph``

    :param appid: The app's id which the item belows to
    :param market_hash_name: The value of the item's market_hash_name
    :return: item_nameid
    :rtype int
    :raises (UnknownSteamErrorException, RequestException)
    """
    url = 'https://steamcommunity.com/market/listings/%d/%s' % (appid, quote(market_hash_name))
    rp = requests_get(url=url)
    if rp.status_code != 200:
        logger.error("Error when getting item_nameid")
        logger.debug(rp.content)
        raise UnknownSteamErrorException('Error when getting item_nameid')
    try:
        # The item_nameid is in js code so I just use regex
        return int(re.search(r'Market_LoadOrderSpread\(\s*\d+\s*\)', rp.text, re.ASCII)[0].split()[1])
    except TypeError:
        logger.error("Error when getting item_nameid")
        logger.debug(rp.text)
        raise UnknownSteamErrorException('Error when getting item_nameid')


def get_item_price_graph(item_nameid: int, currency: int, language: str = 'english') -> Dict:
    """
    Get the item's price graph

    :param item_nameid: item_nameid from function ``get_item_nameid``
    :param currency: user's steam account wallet currency number
    :param language: Preferred language
    :return: {'highest_buy_order': float, 'lowest_sell_order': float,
     'buy_order_graph': List[List[(float)price, (int)amount, (str)comment]],
     'sell_order_graph': List[List[(float)price, (int)amount, (str)comment]]}}
    :raises (UnknownSteamErrorException, RequestException, ApiDoesntReturnSuccessException)
    """
    url = 'https://steamcommunity.com/market/itemordershistogram'
    params = {
        'item_nameid': item_nameid,
        'language': language,
        'currency': currency
    }
    rp = requests_get(url=url, params=params)
    if rp.status_code != 200:
        logger.error("Error when getting item price graph")
        logger.debug(rp.content)
        raise UnknownSteamErrorException('Error when getting item price graph')
    try:
        data = loads(rp.text)  # TODO: vpn断开连接时可能导致数据传输不完整
    except JSONDecodeError:
        logger.error("The steam didn't response right content when get_item_price_graph")
        logger.debug(rp.content)
        raise UnknownSteamErrorException("The steam didn't response right content")
    if not data or data.get('success', 0) != 1:  # Error when steam getting inventory
        logger.error("The get_item_price_graph API doesn't return a right response.")
        logger.debug(data)
        raise ApiDoesntReturnSuccessException("The get_item_price_graph API doesn't return a right response.")
    try:
        return {
            'highest_buy_order': int(data['highest_buy_order']) / 100
            if isinstance(data['highest_buy_order'], str) else None,
            'lowest_sell_order': int(data['lowest_sell_order']) / 100
            if isinstance(data['lowest_sell_order'], str) else None,
            'buy_order_graph': data['buy_order_graph'] if len(data['buy_order_graph']) > 0 else None,
            'sell_order_graph': data['sell_order_graph'] if len(data['sell_order_graph']) > 0 else None
        }
    except ValueError:
        logger.error("Didn't get the right price graph.")
        logger.debug(data)
        raise UnknownSteamErrorException("Didn't get the right price graph.")


def sell_item_on_market(steam_login_secure: str, steam_id: str, app_id: int, context_id: str,
                        assetid: str, amount: str, price: int, language: str = 'english') -> Dict:
    """
    List the item on the market

    :param steam_login_secure: The cookie of the browser that has logged in to the steam account
    :param steam_id: The steam id logged in
    :param app_id: The app's id which the item belows to
    :param context_id: The in-app inventory category id you want to get the inventory
    :param assetid: The assetid of the item
    :param amount: the quantity sold
    :param price: The item price
    :param language: Preferred language
    :return: {'success': bool, 'requires_confirmation': int = 0/1, 'needs_mobile_confirmation': bool,
              'needs_email_confirmation': bool, 'email_domain': str}
    :raises (UnknownSteamErrorException, RequestException, ApiDoesntReturnSuccessException)
    """
    # 税率economy_v2.js的第4469行
    url = 'https://steamcommunity.com/market/sellitem/'
    headers = {
        'Referer': 'https://steamcommunity.com/profiles/%s/inventory/' % steam_id  # Steam checks this too
    }
    data = {
        'sessionid': '000000000000000000000000',  # Steam will check whether sessionid is same as the one in cookie
        'appid': app_id,
        'contextid': context_id,
        'assetid': assetid,
        'amount': amount,
        'price': price
    }
    cookies = {
        'steamLoginSecure': steam_login_secure,
        'sessionid': '000000000000000000000000',
        'Steam_Language': language
    }
    rp = requests_post(url=url, headers=headers, data=data, cookies=cookies)
    if rp.status_code != 200:
        logger.error('Error when listing item on market')
        logger.debug(rp.content)
        raise UnknownSteamErrorException('Error when listing item on market')
    try:
        data = loads(rp.text)  # TODO: vpn断开连接时可能导致数据传输不完整
    except JSONDecodeError:
        logger.error("The steam didn't response right content when sell_item_on_market")
        logger.debug(rp.content)
        raise UnknownSteamErrorException("The steam didn't response right content")
    if not data:
        raise ApiDoesntReturnSuccessException("The sell_item_on_market API doesn't return a right response.")
    return data
