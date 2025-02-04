from datetime import datetime
from typing import Optional

from odev.plugins.odev_rolling_release.api.dtos.Subscription import Subscription
from odev.plugins.odev_rolling_release.api.dtos.UpgradeRequest import UpgradeRequest
from odev.plugins.odev_rolling_release.utils.utils import BoolStr


class Database:
    id: Optional[int]  # pylint: disable=W0622
    version: str
    db_name: str
    db_uuid: str
    parent_id: bool
    subscription: Subscription = Subscription()
    subscription_id: Optional[int]
    upgrade_request: Optional[UpgradeRequest] = None
    date_valid: Optional[datetime]

    def __init__(
        self,
        id: Optional[int] = None,  # pylint: disable=W0622
        version: str = "NO VERSION",
        db_name: str = "NO NAME",
        db_uuid: str = "",
        parent_id: bool = False,
        subscription_id: Optional[int] = None,
        date_valid: Optional[str] = "",
        **kwargs,
    ):
        self.id = id
        self.version = version
        self.db_name = db_name
        self.db_uuid = db_uuid
        self.parent_id = BoolStr(parent_id)
        self.subscription_id = subscription_id
        self.date_valid = datetime.strptime(date_valid, "%Y-%m-%d %H:%M:%S") if date_valid else None

    def get_date_valid(self) -> str:
        return self.date_valid.strftime("%d-%m-%Y") if self.date_valid else ""

    def __repr__(self) -> str:
        return f"DatabaseDTO({self.id}, {self.db_name})"
