from datetime import datetime, timedelta
from typing import Any, List

from odev.plugins.odev_rolling_release.api.strategy.by_title import RollingByTitleStrategy
from odev.plugins.odev_rolling_release.dtos.Task import Task


class RollingByBs4Strategy(RollingByTitleStrategy):
    def _get_tasks_fields(self) -> List[str]:
        values = super()._get_tasks_fields()
        values.append("description")
        return values

    def _get_databases_domain(self, tasks: List[Task]) -> List[Any]:
        today = datetime.now()
        return [
            "&",
            ["url", "in", [task.database_url for task in tasks]],
            ["last_ping", ">", (today - timedelta(days=30)).strftime("%Y-%m-%d")],
        ]
