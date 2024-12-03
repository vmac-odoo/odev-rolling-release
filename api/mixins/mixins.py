from abc import ABC, abstractmethod
from itertools import groupby
from typing import Any, Callable, List, Optional

from odev.common.connectors.rpc import Model, RpcConnector
from odev.common.console import TableHeader
from odev.common.databases.remote import RemoteDatabase

from odev.plugins.odev_rolling_release.dtos.Database import Database
from odev.plugins.odev_rolling_release.dtos.Subscription import Subscription
from odev.plugins.odev_rolling_release.dtos.Task import Task
from odev.plugins.odev_rolling_release.dtos.UpgradeRequest import UpgradeRequest
from odev.plugins.odev_rolling_release.utils.osv import AND
from odev.plugins.odev_rolling_release.utils.utils import TripleFlag


class RollingMixing(ABC):

    odoo_url: str
    upgrade_url: str
    odoo_rpc: RpcConnector
    upgrade_rpc: RpcConnector
    task_domain: List[Any]
    limit: int
    task_name: str | None = None
    with_parent: TripleFlag = TripleFlag.BOTH
    with_contract: TripleFlag = TripleFlag.BOTH
    show_sub: bool = False
    hide_not_found: bool = True
    lucky: bool = False
    upgrade_enabled: bool = False

    def __init__(
        self,
        odoo_url: str,
        odoo_database: str,
        limit: int,
        task_domain: List[Any],
        upgrade_enabled: bool = False,
        upgrade_url: str | None = None,
        upgrade_database: str | None = None,
    ):
        self.odoo_url = f"https://{odoo_url}"
        self.odoo_rpc = RpcConnector(RemoteDatabase(self.odoo_url, odoo_database))
        self.upgrade_enabled = upgrade_enabled
        if self.upgrade_enabled:
            self.upgrade_url = f"https://{upgrade_url}"
            self.upgrade_rpc = RpcConnector(RemoteDatabase(upgrade_url, upgrade_database))
        self.task_domain = task_domain
        self.limit = limit

    def search(self) -> List[List[TableHeader] | List[dict]]:
        tasks = self._get_tasks()
        databases = self._get_databases(tasks)

        subs = (
            self._get_subs([database.subscription_id for database in databases if database.subscription_id])
            if self.show_sub
            else None
        )
        upgrade_requests = (
            self._get_upgrade_request([database.db_uuid for database in databases if database.db_uuid])
            if self.upgrade_enabled
            else None
        )

        tasks_info = self._transform_to_rows(self._merge_records(tasks, databases, subs, upgrade_requests))
        return self._display_task_list(tasks_info)

    def stats(self, group_by: List[str], union_wrapper: Optional[Callable]) -> List[List[Any]]:
        tasks = self._get_tasks()
        return self._display_stats_list(
            self._clean_stats(
                self._get_model("openerp.enterprise.database").read_group(
                    domain=self._get_databases_domain(tasks),
                    groupby=group_by,
                    limit=self.limit,
                ),
                union_wrapper,
            ),
            group_by[0],
        )

    def _get_model(self, model: str, upgrade_mode: bool = False) -> Model:
        return Model(self.odoo_rpc if not upgrade_mode else self.upgrade_rpc, model)

    def _add_extra_config_domains(self, domain: List[Any]) -> List[Any]:
        extra_domains = [
            ("parent_id", self.with_parent),
            ("subscription_id", self.with_contract),
        ]
        for domain_name, value in extra_domains:
            if value != TripleFlag.BOTH:
                new_domain = [([domain_name, "!=", False] if value == TripleFlag.YES else [domain_name, "=", False])]
                domain = AND([domain, new_domain])
        return domain

    def _get_tasks(self) -> List[Task]:
        response: List[dict] = self._get_model("project.task").search_read(
            domain=self._get_tasks_domain(),
            fields=self._get_tasks_fields(),
            limit=self.limit,
        )
        return [Task(**row) for row in response]

    def _get_databases(self, tasks: List[Task]) -> List[Database]:
        response: List[dict] = self._get_model("openerp.enterprise.database").search_read(
            domain=self._add_extra_config_domains(self._get_databases_domain(tasks)),
            fields=self._get_databases_fields(),
            limit=self.limit,
        )

        return [Database(**row) for row in response]

    def _get_subs(self, sub_ids: List[int]) -> List[Subscription]:
        response: List[dict] = self._get_model("sale.order").search_read(
            domain=self._get_subs_domain(sub_ids), fields=self._get_subs_fields(), limit=self.limit
        )
        return [Subscription(**row) for row in response]

    def _get_upgrade_request(self, databases: List[Database]) -> List[UpgradeRequest]:
        response: List[dict] = self._get_model("upgrade.request", True).search_read(
            domain=self._get_upgrade_request_domain(databases),
            fields=self._get_upgrade_request_fields(),
            limit=self.limit,
        )
        response.sort(key=lambda r: r["db_uuid"])
        requests = []
        for _, group in groupby(response, lambda r: r["db_uuid"]):
            requests.append(max(group, key=lambda x: x["id"]))
        return [UpgradeRequest(**row) for row in requests]

    def _clean_stats(self, datalist: List[dict], union_wrapper: Callable | None):
        return datalist if not callable(union_wrapper) else union_wrapper(datalist)

    @abstractmethod
    def _get_tasks_domain(self) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_tasks_fields(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def _get_databases_domain(self, tasks: List[dict]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_databases_fields(self) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_subs_domain(self, sub_ids: List[int]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_subs_fields(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def _get_upgrade_request_domain(self, db_uuid_list: List[str]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_upgrade_request_fields(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def _merge_records(
        self,
        tasks: List[Task],
        databases: List[Database],
        subs: Optional[List[Subscription]],
        upgrade_request: Optional[List[UpgradeRequest]],
    ) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def _transform_to_rows(self, tasks: List[Task]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _display_task_list(self, rows: List[List[Any]]) -> List[List[TableHeader] | List[dict]]:
        raise NotImplementedError

    @abstractmethod
    def _display_stats_list(self, rows: List[dict], group_title: str) -> List[List[TableHeader] | List[dict]]:
        raise NotImplementedError
