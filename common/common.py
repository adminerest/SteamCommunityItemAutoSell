from datetime import datetime, timezone

MONTH = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12
}


def parse_datetime(datetime_str: str) -> datetime:
    """
    Change Steam datetime string into :class:``datetime``

    :param datetime_str: datetime string
    :return: :class:``datetime``
    :raises (IndexError, KeyError, ValueError)
    """
    datetime_list = datetime_str.replace(':', '').split()
    return datetime(int(datetime_list[2]), MONTH[datetime_list[0]],
                    int(datetime_list[1]), int(datetime_list[3]), tzinfo=timezone.utc)

