class SteamException(Exception):
    """There was an ambiguous exception that occurred while using Steam api."""


class InventoryPrivateException(SteamException):
    """Steam inventory is private"""


class UnknownSteamErrorException(SteamException):
    """Unknown Steam error"""


class ApiDoesntReturnSuccessException(SteamException):
    """Api responses success != 1 or error"""


class ApiDoesntReturnNeededParameterException(SteamException):
    """Api doesn't return the needed parameter"""


class LoginCookieExpiredException(SteamException):
    """The login cookie ``steamLoginSecure`` is wrong"""
