from typing import Any, List, Optional

from bs4 import BeautifulSoup

from odev.plugins.odev_rolling_release.api.dtos.Database import Database


class Task:
    id: int  # pylint: disable=W0622
    name: str
    show_sub: bool = False
    upgrade_mode: bool = False
    description: Optional[str]
    database: Database = Database()

    def __init__(
        self,
        id: int,
        name: str,
        description: str = None,
        show_sub: bool = False,
        upgrade_mode: bool = False,
        **kwargs,
    ):  # pylint: disable=W0622
        self.id = id
        self.name = name
        self.description = description
        self.show_sub = show_sub
        self.upgrade_mode = upgrade_mode

    @property
    def display_name(self) -> str:
        return self.name.replace("[rr] ", "")

    @property
    def database_url(self) -> str:
        if not self.description:
            return ""
        url = BeautifulSoup(self.description, "html.parser").find("a", href=True)
        return url["href"].replace("/_odoo/support", "")

    def task_link(self, odoo_url: str = "") -> str:
        return f"{odoo_url}/odoo/my-tasks/{self.id}"

    def get_clean_row(self, odoo_url: str = "") -> List[Any]:
        rows = [
            self.name,
            self.database.version,
            str(self.database.subscription.get_sub_value(self.show_sub)),
            str(self.database.parent_id),
            self.database.get_date_valid(),
            self.task_link(odoo_url),
        ]
        if self.upgrade_mode:
            rows.insert(4, str(self.database.upgrade_request.has_traceback))
        return rows

    def __repr__(self) -> str:
        return f"TaskDTO({self.id}, {self.name})"
