import re
from typing import Dict, Union
from json import loads
from os.path import dirname


class Config(object):
    debug: bool = False  # Enable debug log
    proxy: Dict = {}  # Set proxy
    mobile_confirmation: bool = False  # Need mobile confirmation after list on market
    language: str = 'english'  # !important the language user preferred
    steam_login_secure: str = None  # The steam website cookie
    steam_id: str = None  # Steam id
    app_id: int = 753  # The game which want to sell
    context_id: str = '6'  # The game's context id which want to sell
    allow_to_sell_item = {
        'enable': True,
        'item_type': set()  # Type: int
    }
    disallow_to_sell_item = {
        'enable': False,
        'item_type': set()  # Type: int
    }
    allow_to_sell_item_detail = {
        'enable': False,
        'item_detail_type': set()  # Type: str
    }
    disallow_to_sell_item_detail = {
        'enable': False,
        'item_detail_type': set()  # Type: sstr
    }
    price_setting = {
        'lowest_price': None,  # Type: float; The item selling price must above the lowest_price
        'highest_price': None,  # Type: float; The item selling price must lower than the highest_price
        'calculation_formula': None,  # Type: str; The calculation formula
        'least_sells_hours': 36,  # In least_sells_hours must have hours_least_sells
        'hours_least_sells': 25,  # In least_sells_hours must have hours_least_sells
        'least_sell_orders': 20,  # The item must have least_sell_orders sell orders now
        'least_buy_orders': 0,  # The item must have least_buy_orders buy orders now
        'normal_card': {
            'lowest_price': None,  # Type: float; The normal card selling price must above the lowest_price
            'highest_price': None  # Type: float; The normal card selling price must lower than the highest_price
        },
        'foil_card': {
            'lowest_price': None,  # Type: float; The foil card selling price must above the lowest_price
            'highest_price': None  # Type: float; The foil card selling price must lower than the highest_price
        },
        'other_item': {
            'lowest_price': None,  # Type: float; The other items' selling price must above the lowest_price
            'highest_price': None  # Type: float; The other items' selling price must lower than the highest_price
        }
    }

    __MUST_CONFIG = (  # The params in this set must be configured
        'self.steam_login_secure',
        'self.steam_id',
        "self.price_setting['calculation_formula']",
    )

    __CONFIG_TYPE = {  # The config params type
        'debug': (bool,),
        'proxy': (str,),
        'mobile_confirmation': (bool,),
        'language': (str,),
        'steam_login_secure': (str,),
        'steam_id': (str,),
        'app_id': (int,),
        'context_id': (int, str),
        'allow_to_sell_item': (dict,),
        'allow_to_sell_item_value': {
            'enable': (bool,),
            'item_type': (set,),
            'item_type_value': int
        },
        'disallow_to_sell_item': (dict,),
        'disallow_to_sell_item_value': {
            'enable': (bool,),
            'item_type': (set,),
            'item_type_value': int
        },
        'allow_to_sell_item_detail': (dict,),
        'allow_to_sell_item_detail_value': {
            'enable': (bool,),
            'item_detail_type': (set,),
            'item_detail_type_value': str,
        },
        'disallow_to_sell_item_detail': (dict,),
        'disallow_to_sell_item_detail_value': {
            'enable': (bool,),
            'item_detail_type': (set,),
            'item_detail_type_value': str,
        },
        'price_setting': (dict,),
        'price_setting_value': {
            'lowest_price': (float, int, type(None)),
            'highest_price': (float, int, type(None)),
            'calculation_formula': (str,),
            'least_sells_hours': (int,),
            'hours_least_sells': (int,),
            'least_sell_orders': (int,),
            'least_buy_orders': (int,),
            'normal_card': (dict, type(None)),
            'normal_card_value': {
                'lowest_price': (float, int, type(None)),
                'highest_price': (float, int, type(None))
            },
            'foil_card': (dict, type(None)),
            'foil_card_value': {
                'lowest_price': (float, int, type(None)),
                'highest_price': (float, int, type(None))
            },
            'other_item': (dict, type(None)),
            'other_item_value': {
                'lowest_price': (float, int, type(None)),
                'highest_price': (float, int, type(None))
            }
        }
    }

    def __init__(self):
        data = self.__load_config()
        self.__check_config_type(data)
        self.__set_config(data)
        self.__check_must_config()

    def __check_config_type(self, config_data: Dict) -> None:
        """
        Check json file parameters type

        :param config_data: the raw config dict
        :return: None
        :raises (ConfigFileErrorException)
        """
        if not isinstance(config_data, dict):
            raise ConfigFileErrorException('Json is not a dict')

        def __check_dict(dict_data: Dict, cmp_dict: Dict):
            for k in dict_data.keys():
                if cmp_dict.get(k, False):
                    if cmp_dict.get(k) == set or set in cmp_dict.get(k):
                        if isinstance(dict_data[k], list):
                            for data in dict_data[k]:
                                if not isinstance(data, cmp_dict.get(k + '_value')):
                                    raise ConfigFileErrorException('Key: %s is in a wrong format' % k)
                        elif isinstance(dict_data[k], cmp_dict.get(k)):
                            pass
                        else:
                            raise ConfigFileErrorException('Key: %s is in a wrong format' % k)
                    elif cmp_dict.get(k) == dict or dict in cmp_dict.get(k):
                        if isinstance(dict_data[k], cmp_dict.get(k)):
                            __check_dict(dict_data[k], cmp_dict.get(k + '_value'))
                        else:
                            raise ConfigFileErrorException('Key: %s is in a wrong format' % k)
                    else:
                        if not isinstance(dict_data[k], cmp_dict.get(k)):
                            raise ConfigFileErrorException('Key: %s is in a wrong format' % k)

        __check_dict(config_data, self.__CONFIG_TYPE)

    def __check_must_config(self) -> None:
        """
        Check whether the must config is set or not

        :return: None
        :raises (KeyNotConfigException)
        """
        for config_key in self.__MUST_CONFIG:
            if eval(config_key) is None:
                raise KeyNotConfigException('The must config not set')

    def __set_config(self, config_data: Dict) -> None:
        """
        Set the config object

        :param config_data: the raw config dict
        :return: None
        :raises (ConfigFileErrorException)
        """

        self.debug: bool = config_data.get('debug', False)

        proxy: str = config_data.get('proxy', '')
        if proxy != '':
            if not re.match(r'http|socks5|https://.*', proxy):
                raise ConfigFileErrorException('Key: proxy is in a wrong format')
            else:
                self.proxy = {
                    'http': proxy,
                    'https': proxy
                }
        else:
            self.proxy = {}

        self.mobile_confirmation: bool = config_data.get('mobile_confirmation', False)

        self.language: str = config_data.get('language', 'english')

        self.steam_login_secure: str = config_data.get('steam_login_secure', '').upper().replace('%7C', '|')

        self.steam_id: str = config_data.get('steam_id', '')
        if len(self.steam_id) != 17:
            raise ConfigFileErrorException('Key: steam_id is in a wrong format')

        self.app_id: int = config_data.get('app_id', 753)
        self.context_id: str = config_data.get('context_id', 6)

        self.allow_to_sell_item = config_data.setdefault('allow_to_sell_item', {'enable': True, 'item_type': set()})
        self.allow_to_sell_item['enable'] = config_data.get('allow_to_sell_item').get('enable', True)
        self.allow_to_sell_item['item_type'] = set(config_data.get('allow_to_sell_item').get('item_type', set()))

        self.disallow_to_sell_item = config_data.setdefault('disallow_to_sell_item', {'enable': False,
                                                                                      'item_type': set()})
        self.disallow_to_sell_item['enable'] = config_data.get('disallow_to_sell_item').get('enable', False)
        self.disallow_to_sell_item['item_type'] = set(config_data.get('disallow_to_sell_item').get('item_type', set()))

        self.allow_to_sell_item_detail = config_data.setdefault('allow_to_sell_item_detail', {'enable': False,
                                                                                              'item_detail_type': set()
                                                                                              })
        self.allow_to_sell_item_detail['enable'] = config_data.get('allow_to_sell_item_detail').get('enable', False)
        self.allow_to_sell_item_detail['item_detail_type'] = set(config_data.get('allow_to_sell_item_detail')
                                                                 .get('item_detail_type', set()))

        self.disallow_to_sell_item_detail = config_data.setdefault('disallow_to_sell_item_detail',
                                                                   {'enable': False, 'item_detail_type': set()})
        self.disallow_to_sell_item_detail['enable'] = config_data.get('disallow_to_sell_item_detail').get('enable',
                                                                                                          False)
        self.disallow_to_sell_item_detail['item_detail_type'] = set(config_data.get('disallow_to_sell_item_detail')
                                                                    .get('item_detail_type', set()))

        self.price_setting = config_data.setdefault('price_setting', {'lowest_price': None,
                                                                      'highest_price': None,
                                                                      'calculation_formula': None,
                                                                      'least_sells_hours': 36,
                                                                      'hours_least_sells': 25,
                                                                      'least_sell_orders': 20,
                                                                      'least_buy_orders': None,
                                                                      'normal_card': {
                                                                          'lowest_price': None,
                                                                          'highest_price': None
                                                                      },
                                                                      'foil_card': {
                                                                          'lowest_price': None,
                                                                          'highest_price': None
                                                                      },
                                                                      'other_item': {
                                                                          'lowest_price': None,
                                                                          'highest_price': None
                                                                      }})

        def __price_check(price: Union[int, float], key_name: str) -> float:
            if price is not None:
                if price < 0.0:
                    raise ConfigFileErrorException("Key: %s isn't correct" % key_name)
                else:
                    return float(price)

        self.price_setting['lowest_price'] = __price_check(config_data.get('price_setting').get('lowest_price', None),
                                                           'price_setting.lowest_price')

        self.price_setting['highest_price'] = __price_check(config_data.get('price_setting').get('highest_price', None),
                                                            'price_setting.highest_price')
        if self.price_setting['highest_price'] is not None and \
                self.price_setting['lowest_price'] is not None and \
                self.price_setting['highest_price'] < self.price_setting['lowest_price']:
            raise ConfigFileErrorException("Key: price_setting.highest_price or "
                                           "price_setting.lowest_price isn't correct")

        self.price_setting['calculation_formula'] = config_data.get('price_setting').get('calculation_formula', None)

        def __check_int(num: int, key_name: str) -> None:
            if num < 0:
                raise ConfigFileErrorException("Key: %s isn't correct" % key_name)

        self.price_setting['least_sells_hours'] = config_data.get('price_setting').get('least_sells_hours', 36)
        __check_int(self.price_setting['least_sells_hours'], 'price_setting.least_sells_hours')

        self.price_setting['hours_least_sells'] = config_data.get('price_setting'
                                                                  ).get('hours_least_sells',
                                                                        25)
        __check_int(self.price_setting['hours_least_sells'],
                    'price_setting.hours_least_sells')

        self.price_setting['least_sell_orders'] = config_data.get('price_setting').get('least_sell_orders', 25)
        __check_int(self.price_setting['least_sell_orders'], 'price_setting.least_sell_orders')

        self.price_setting['least_buy_orders'] = config_data.get('price_setting').get('least_buy_orders', 0)
        __check_int(self.price_setting['least_buy_orders'], 'price_setting.least_buy_orders')

        self.price_setting['normal_card'] = config_data.get('price_setting').setdefault('normal_card',
                                                                                        {'lowest_price': None,
                                                                                         'highest_price': None})

        self.price_setting['normal_card']['lowest_price'] = __price_check(config_data.get('price_setting')
                                                                          .get('normal_card')
                                                                          .get('lowest_price', None),
                                                                          'price_setting.normal_card.lowest_price')

        self.price_setting['normal_card']['highest_price'] = __price_check(config_data.get('price_setting')
                                                                           .get('normal_card')
                                                                           .get('highest_price', None),
                                                                           'price_setting.normal_card.highest_price')

        self.price_setting['foil_card'] = config_data.get('price_setting').setdefault('foil_card',
                                                                                      {'lowest_price': None,
                                                                                       'highest_price': None})

        self.price_setting['foil_card']['lowest_price'] = __price_check(config_data.get('price_setting')
                                                                        .get('foil_card')
                                                                        .get('lowest_price', None),
                                                                        'price_setting.foil_card.lowest_price')

        self.price_setting['foil_card']['highest_price'] = __price_check(config_data.get('price_setting')
                                                                         .get('foil_card')
                                                                         .get('highest_price', None),
                                                                         'price_setting.foil_card.highest_price')

        self.price_setting['foil_card'] = config_data.get('price_setting').setdefault('foil_card',
                                                                                      {'lowest_price': None,
                                                                                       'highest_price': None})

        self.price_setting['other_item']['lowest_price'] = __price_check(config_data.get('price_setting')
                                                                         .get('other_item')
                                                                         .get('lowest_price', None),
                                                                         'price_setting.other_item.lowest_price')

        self.price_setting['other_item']['highest_price'] = __price_check(config_data.get('price_setting')
                                                                          .get('other_item')
                                                                          .get('highest_price', None),
                                                                          'price_setting.other_item.highest_price')

    @staticmethod
    def __load_config() -> Dict:
        """
        Load config file

        :return: Config Dict
        :rtype Dict
        :raises (FileNotFoundError, JSONDecodeError)
        """
        path = dirname(__file__) + '/config.json'
        f = open(path, 'r', encoding='utf-8')
        configs = f.read()
        f.close()
        return loads(configs)


class ConfigFileErrorException(Exception):
    """The config json is not in a right format"""


class KeyNotConfigException(Exception):
    """The must config not set"""


config = Config()
