from typing import Optional

from odev.plugins.odev_rolling_release.utils.utils import BoolStr


class UpgradeRequest:
    id: Optional[int]  # pylint: disable=W0622
    db_uuid: str
    last_traceback: Optional[str] = None

    def __init__(
        self, id: int = None, db_uuid: str = "", last_traceback: Optional[str] = None, **kwargs  # pylint: disable=W0622
    ):
        self.id = id
        self.db_uuid = db_uuid
        self.last_traceback = last_traceback

    @property
    def has_traceback(self) -> BoolStr:
        return BoolStr(self.last_traceback)

    def __repr__(self) -> str:
        return f"UpgradeRequestDTO({self.id}, {self.db_uuid})"
