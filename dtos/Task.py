from typing import Any, List, Optional

from bs4 import BeautifulSoup

from odev.plugins.odev_rolling_release.dtos.Database import Database


class Task:
    id: int  # pylint: disable=W0622
    name: str
    description: Optional[str]
    database: Database = Database()

    def __init__(self, id: int, name: str, description: str = None, **kwargs):  # pylint: disable=W0622
        self.id = id
        self.name = name
        self.description = description

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

    def get_clean_row(self, odoo_url: str = "", show_sub: bool = False, upgrade_enabled: bool = False) -> List[Any]:
        rows = [
            self.name,
            self.database.version,
            str(self.database.subscription.get_sub_value(show_sub)),
            str(self.database.parent_id),
            self.task_link(odoo_url),
        ]
        if upgrade_enabled:
            rows.insert(4, str(self.database.upgrade_request.has_traceback))
        return rows
