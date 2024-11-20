from collections import defaultdict
from enum import Enum
from typing import Any, Callable, List


class TripleFlag(Enum):
    YES = "YES"
    NO = "NO"
    BOTH = "BOTH"

    def __str__(self) -> str:
        return self.value


class BoolStr:
    def __init__(self, value: Any, value_if_true=False):
        self.value, self.value_if_true = value, value_if_true

    def __str__(self) -> str:
        if self.value and self.value_if_true:
            return self.value
        return "YES" if self.value else "NO"


def list_to_dict(data_list: List[dict], key_func: Callable[[dict], str]) -> dict:
    new_dict = {}
    for data in data_list:
        key = key_func(data)
        new_dict[key] = data
    return new_dict


def yes_or_no_value(value) -> str:
    return "YES" if value else "NO"


def group_by_record_exists(datalist: List[dict], key: str) -> List[dict]:
    result: defaultdict[str, int] = defaultdict(int)
    for item in datalist:
        item[key] = yes_or_no_value(bool(item[key]))
        result[item[key]] += item["__count"]
    return [{key: k, "__count": v} for k, v in result.items()]
