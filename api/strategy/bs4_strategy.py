from datetime import datetime, timedelta
from typing import Any, List

from odev.plugins.odev_rolling_release.api.dtos.Task import Task
from odev.plugins.odev_rolling_release.api.strategy.title_strategy import TitleStrategy


class Bs4Strategy(TitleStrategy):
    def _task_fields(self) -> List[str]:
        domain = super()._task_fields()
        domain.append("description")
        return domain

    def _get_database_domain(self, tasks: List[Task]) -> List[Any]:
        today = datetime.now()
        domain = [
            "&",
            ["url", "in", [task.database_url for task in tasks]],
            ["last_ping", ">", (today - timedelta(days=30)).strftime("%Y-%m-%d")],
        ]
        return self._add_database_extra_config_domains(domain)
