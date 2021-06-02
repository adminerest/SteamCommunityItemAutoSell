from typing import Dict
from math import floor


class Wallet(object):
    wallet_fee_base: int
    wallet_fee_percent: float
    wallet_fee_minimum: int
    currency: int
    wallet_publisher_fee_percent_default: float

    def __init__(self, wallet_fee_base: int, wallet_fee_percent: float, wallet_fee_minimum: int,
                 currency: int, wallet_publisher_fee_percent_default: float):
        self.wallet_fee_base: int = wallet_fee_base
        self.wallet_fee_percent: float = wallet_fee_percent
        self.wallet_fee_minimum: int = wallet_fee_minimum
        self.currency: int = currency
        self.wallet_publisher_fee_percent_default: float = wallet_publisher_fee_percent_default

    def calculate_fee(self, sell_price: float, publisher_fee_percent: float = None) -> float:
        """
        Calculate the steam market fee

        :param sell_price: The buyer need to pay
        :param publisher_fee_percent: The item's publisher fee percent
        :return: The total fee
        """
        if publisher_fee_percent is None:
            publisher_fee_percent = self.wallet_publisher_fee_percent_default
        iterations = 0
        sell_price = int(sell_price * 100.0)
        estimated_received = int((sell_price - self.wallet_fee_base) / (self.wallet_fee_percent +
                                                                        publisher_fee_percent + 1))
        ever_undershot = False

        def __calculate_amount_desired_received(received_amount: int,
                                                publisher_fee_percentage: float) -> Dict[str, int]:
            steam_fee = int(
                floor(
                    max(received_amount * self.wallet_fee_percent, self.wallet_fee_minimum) + self.wallet_fee_base))
            publisher_fee = int(
                floor(
                    max(
                        received_amount * publisher_fee_percentage, 1.0) if publisher_fee_percentage > 0 else 0))
            amount_to_send = received_amount + steam_fee + publisher_fee
            return {
                'steam_fee': steam_fee,
                'publisher_fee': publisher_fee,
                'fees': steam_fee + publisher_fee,
                'amount': amount_to_send
            }

        fees = __calculate_amount_desired_received(estimated_received, publisher_fee_percent)
        while fees['amount'] != sell_price and iterations < 10:
            if fees['amount'] > sell_price:
                if ever_undershot:
                    fees = __calculate_amount_desired_received(estimated_received - 1, publisher_fee_percent)
                    fees['steam_fee'] += (sell_price - fees['amount'])
                    fees['fees'] += (sell_price - fees['amount'])
                    fees['amount'] = sell_price
                    break
                else:
                    estimated_received -= 1
            else:
                ever_undershot = True
                estimated_received += 1
            fees = __calculate_amount_desired_received(estimated_received, publisher_fee_percent)
            iterations += 1
        return fees['fees']

