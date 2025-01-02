import random
from datetime import datetime, timedelta
from typing import Any, Callable, List, Optional

from odev.common.connectors.rpc import RpcConnector
from odev.common.console import TableHeader

from odev.plugins.odev_rolling_release.api.dtos.Database import Database
from odev.plugins.odev_rolling_release.api.dtos.Subscription import Subscription
from odev.plugins.odev_rolling_release.api.dtos.Task import Task
from odev.plugins.odev_rolling_release.api.dtos.UpgradeRequest import UpgradeRequest
from odev.plugins.odev_rolling_release.api.services.database_service import DatabaseService
from odev.plugins.odev_rolling_release.api.services.sale_order_service import SaleOrderService
from odev.plugins.odev_rolling_release.api.services.task_service import TaskService
from odev.plugins.odev_rolling_release.api.services.upgrade_request_service import UpgradeRequestService
from odev.plugins.odev_rolling_release.api.strategy.strategy_abstract import Strategy
from odev.plugins.odev_rolling_release.utils.osv import AND
from odev.plugins.odev_rolling_release.utils.utils import TripleFlag, list_to_dict


class TitleStrategy(Strategy):
    def __init__(
        self,
        task_domain: List[Any],
        limit: int,
        odoo_rpc: RpcConnector,
        upgrade_rpc: Optional[RpcConnector] = None,
        odoo_url: str = "",
    ):
        super().__init__(task_domain, limit, odoo_rpc, upgrade_rpc, odoo_url)
        self.task_service = TaskService(odoo_rpc)
        self.database_service = DatabaseService(odoo_rpc)
        self.sale_order_service = SaleOrderService(odoo_rpc)
        if upgrade_rpc:
            self.upgrade_request_service = UpgradeRequestService(upgrade_rpc)

    def _task_fields(self) -> List[str]:
        # To be able to override and not create monkeypatches
        return ["name"]

    def _get_tasks_domain(self) -> List[Any]:
        domain = self.task_domain
        if self.task_name:
            new_domain = [["name", "ilike", f"%{self.task_name}%"]]
            domain = AND([domain, new_domain])
        return domain

    def _add_database_extra_config_domains(self, domain: List[Any]) -> List[Any]:
        extra_domains = [
            ("parent_id", self.parent),
            ("subscription_id", self.contract),
        ]
        for domain_name, value in extra_domains:
            if value != TripleFlag.BOTH:
                new_domain = [([domain_name, "!=", False] if value == TripleFlag.YES else [domain_name, "=", False])]
                domain = AND([domain, new_domain])
        return domain

    def _get_databases_domain(self, tasks: List[Task]) -> List[Any]:
        today = datetime.now()
        domain = [
            "&",
            ["db_name", "in", [task.display_name for task in tasks]],
            ["last_ping", ">", (today - timedelta(days=30)).strftime("%Y-%m-%d")],
        ]
        return self._add_database_extra_config_domains(domain)

    def _get_subscription_domain(self, databases: List[Database]) -> List[Any]:
        sub_ids = [database.subscription_id for database in databases if database.subscription_id]
        return [["id", "in", sub_ids]]

    def _get_upgrade_request_domain(self, databases: List[Database]) -> List[Any]:
        db_uuids = [database.db_uuid for database in databases if database.db_uuid]
        return [
            ["db_uuid", "in", db_uuids],
            ["state", "not in", ["new", "pending", "progress", "cancelled"]],
            ["active", "in", [True, False]],
        ]

    def _merge_records(
        self,
        tasks: List[Task],
        databases: List[Database],
        subs: List[Subscription],
        upgrade_request: Optional[List[UpgradeRequest]] = None,
    ) -> List[Task]:
        transformed_tasks = list_to_dict(tasks, lambda task: task.display_name)
        transformed_databases = list_to_dict(databases, lambda database: database.db_name)
        transformed_subs = list_to_dict(subs, lambda sub: sub.id)
        if self.upgrade_rpc and upgrade_request:
            transformed_upgrade_request = list_to_dict(upgrade_request, lambda request: request.db_uuid)
        new_tasks: List[Task] = []
        for key, task in transformed_tasks.items():
            if transformed_databases.get(key) or not self.hide_not_found:
                task.database = transformed_databases.get(key, Database())
                task.database.subscription = transformed_subs.get(task.database.subscription_id, Subscription())
                if self.upgrade_rpc and upgrade_request:
                    task.database.upgrade_request = transformed_upgrade_request.get(
                        task.database.db_uuid, UpgradeRequest()
                    )
                new_tasks.append(task)
        return new_tasks

    def _transform_to_rows(self, tasks: List[Task]) -> List[Any]:
        new_rows = [task.get_clean_row(self.odoo_url) for task in tasks]
        return new_rows if not self.lucky else [random.choice(new_rows)]

    def _display_task_list(self, rows: List[Any]) -> List[List[TableHeader] | List[dict]]:
        titles = [
            TableHeader("Task Name"),
            TableHeader("Version"),
            TableHeader("Sub"),
            TableHeader("Parent"),
            TableHeader("Exp Date"),
            TableHeader(
                "Link",
                min_width=max(len(row[-1]) for row in rows) if len(rows) else 0,
                style="bold color.purple",
            ),
        ]
        if self.upgrade_rpc:
            titles.insert(4, TableHeader("Traceback"))
        return [titles, rows]

    def search(self) -> List[List[TableHeader] | List[dict]]:
        if self.show_sub:
            self.task_service.with_sub()
        if self.upgrade_rpc:
            self.task_service.with_upgrade_mode()
        tasks: List[Task] = (
            self.task_service.with_fields(self._task_fields())
            .with_domain(self._get_tasks_domain())
            .with_limit(self.limit)
            .fetch()
        )
        databases: List[Database] = (
            self.database_service.with_fields(
                [
                    "subscription_id",
                    "version",
                    "url",
                    "extra_apps",
                    "db_name",
                    "db_uuid",
                    "parent_id",
                    "date_valid",
                ]
            )
            .with_domain(self._get_databases_domain(tasks))
            .with_limit(self.limit)
            .fetch()
        )
        subscriptions: List[Subscription] = (
            self.sale_order_service.with_fields(["client_order_ref"])
            .with_domain(self._get_subscription_domain(databases))
            .with_limit(self.limit)
            .fetch()
        )
        upgrade_requests: Optional[List[UpgradeRequest]] = (
            self.upgrade_request_service.with_fields(["db_uuid", "last_traceback"])
            .with_domain(self._get_upgrade_request_domain(databases))
            .with_limit(self.limit)
            .fetch()
            if self.upgrade_rpc
            else None
        )

        tasks_merged: List[Task] = self._merge_records(tasks, databases, subscriptions, upgrade_requests)

        if self.order_by_validity:
            tasks_merged = self._get_ordered_tasks(tasks_merged)

        rows: List[dict] = self._transform_to_rows(tasks_merged)

        return self._display_task_list(rows)

    def _get_ordered_tasks(self, tasks: List[Task]) -> List[Task]:
        tasks = sorted(
            tasks,
            key=lambda task: task.database.date_valid.timestamp()
            if task.database and task.database.date_valid
            else None,
        )
        return tasks

    def _clean_stats(self, datalist: List[dict], union_wrapper: Callable | None):
        return datalist if not callable(union_wrapper) else union_wrapper(datalist)

    def _display_stats_list(self, rows: List[dict], group_title: str) -> List[List[TableHeader] | List[dict]]:
        titles = [
            TableHeader(group_title),
            TableHeader("Count", style="bold color.purple"),
        ]
        return [titles, [[str(row.get(group_title, "")), str(row.get("__count", ""))] for row in rows]]

    def stats(self, group_by: List[str], union_wrapper: Optional[Callable]) -> List[List[Any]]:
        tasks: Task = (
            self.task_service.with_fields(self._task_fields())
            .with_domain(self._get_tasks_domain())
            .with_limit(self.limit)
            .fetch()
        )
        response = (
            self.database_service.with_domain(self._get_databases_domain(tasks))
            .with_limit(self.limit)
            .fetch_group(group_by, union_wrapper)
        )
        return self._display_stats_list(
            response,
            group_by[0],
        )
