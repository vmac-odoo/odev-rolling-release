from typing import Optional

from odev.plugins.odev_rolling_release.utils.utils import BoolStr


class Subscription:
    id: Optional[int]  # pylint: disable=W0622
    client_order_ref: BoolStr

    def __init__(self, id: int = None, client_order_ref: Optional[str] = None, **kwargs):  # pylint: disable=W0622
        self.id = id
        self.client_order_ref = BoolStr(client_order_ref)

    def get_sub_value(self, show_sub: bool = False) -> str:
        self.client_order_ref.value_if_true = show_sub
        return str(self.client_order_ref)
