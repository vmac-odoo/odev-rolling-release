import random
from datetime import datetime, timedelta
from typing import Any, List

from odev.common.console import TableHeader

from odev.plugins.odev_rolling_release.api.mixins.mixins import RollingMixing
from odev.plugins.odev_rolling_release.dtos.Database import Database
from odev.plugins.odev_rolling_release.dtos.Subscription import Subscription
from odev.plugins.odev_rolling_release.dtos.Task import Task
from odev.plugins.odev_rolling_release.dtos.UpgradeRequest import UpgradeRequest
from odev.plugins.odev_rolling_release.utils.osv import AND
from odev.plugins.odev_rolling_release.utils.utils import list_to_dict


class RollingByTitleStrategy(RollingMixing):
    def _get_tasks_domain(self) -> List[Any]:
        domain = self.task_domain
        if self.task_name:
            new_domain = [["name", "ilike", f"%{self.task_name}%"]]
            domain = AND([domain, new_domain])
        return domain

    def _get_tasks_fields(self) -> List[str]:
        return ["id", "name"]

    def _get_databases_domain(self, tasks: List[Task]) -> List[Any]:
        today = datetime.now()
        return [
            "&",
            ["db_name", "in", [task.display_name for task in tasks]],
            ["last_ping", ">", (today - timedelta(days=30)).strftime("%Y-%m-%d")],
        ]

    def _get_databases_fields(self) -> List[Any]:
        return [
            "id",
            "subscription_id",
            "version",
            "url",
            "extra_apps",
            "db_name",
            "db_uuid",
            "parent_id",
        ]

    def _get_subs_domain(self, sub_ids: List[int]) -> List[Any]:
        return [["id", "in", sub_ids]]

    def _get_subs_fields(self) -> List[str]:
        return ["id", "client_order_ref"]

    def _get_upgrade_request_domain(self, db_uuid_list: List[str]) -> List[Any]:
        return [
            ["db_uuid", "in", db_uuid_list],
            ["state", "not in", ["new", "pending", "progress", "cancelled"]],
            ["active", "in", [True, False]],
        ]

    def _get_upgrade_request_fields(self) -> List[str]:
        return ["id", "db_uuid", "last_traceback"]

    def _merge_records(
        self,
        tasks: List[Task],
        databases: List[Database],
        subs: List[Subscription],
        upgrade_request: List[UpgradeRequest],
    ) -> List[Task]:
        transformed_tasks = list_to_dict(tasks, lambda task: task.display_name)
        transformed_databases = list_to_dict(databases, lambda database: database.db_name)

        if self.show_sub:
            transformed_subs = list_to_dict(subs, lambda sub: sub.id)
        if self.upgrade_enabled:
            transformed_upgrade_request = list_to_dict(upgrade_request, lambda request: request.db_uuid)
        new_tasks: List[Task] = []
        for key, task in transformed_tasks.items():
            if transformed_databases.get(key) or not self.hide_not_found:
                task.database = transformed_databases.get(key, Database())
                if self.show_sub:
                    task.database.subscription = transformed_subs.get(task.database.subscription_id, Subscription())
                if self.upgrade_enabled:
                    task.database.upgrade_request = transformed_upgrade_request.get(
                        task.database.db_uuid, UpgradeRequest()
                    )
                new_tasks.append(task)
        return new_tasks

    def _transform_to_rows(self, tasks: List[Task]) -> List[Any]:
        new_rows = [task.get_clean_row(self.odoo_url, self.show_sub, self.upgrade_enabled) for task in tasks]
        return new_rows if not self.lucky else [random.choice(new_rows)]

    def _display_task_list(self, rows: List[List[Any]]) -> List[List[TableHeader] | List[dict]]:
        titles = [
            TableHeader("Task Name"),
            TableHeader("Version"),
            TableHeader("Sub"),
            TableHeader("Parent"),
            TableHeader(
                "Link",
                min_width=max(len(row[-1]) for row in rows),
                style="bold color.purple",
            ),
        ]
        if self.upgrade_enabled:
            titles.insert(4, TableHeader("Traceback"))
        return [titles, rows]

    def _display_stats_list(self, rows: List[dict], group_title: str) -> List[List[TableHeader] | List[dict]]:
        titles = [
            TableHeader(group_title),
            TableHeader("Count", style="bold color.purple"),
        ]
        return [titles, [[str(row.get(group_title, "")), str(row.get("__count", ""))] for row in rows]]
