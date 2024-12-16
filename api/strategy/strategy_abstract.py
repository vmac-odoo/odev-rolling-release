from abc import abstractmethod
from typing import Any, Callable, List, Optional

from typing_extensions import Self

from odev.common.connectors.rpc import RpcConnector
from odev.common.console import TableHeader

from odev.plugins.odev_rolling_release.api.dtos.Task import Task
from odev.plugins.odev_rolling_release.utils.utils import TripleFlag


class Strategy:
    odoo_url: str
    odoo_rpc: RpcConnector
    upgrade_rpc: Optional[RpcConnector] = None
    task_name: Optional[str] = None
    task_domain: List[Any] = []
    limit: int
    parent: TripleFlag = TripleFlag.BOTH
    contract: TripleFlag = TripleFlag.BOTH
    show_sub: bool = False
    hide_not_found: bool = True
    lucky: bool = False
    order_by_validity = False

    def __init__(
        self,
        task_domain: List[Any],
        limit: int,
        odoo_rpc: RpcConnector,
        upgrade_rpc: Optional[RpcConnector] = None,
        odoo_url: str = "",
    ):
        self.odoo_rpc = odoo_rpc
        self.task_domain = task_domain
        self.limit = limit
        self.odoo_rpc = odoo_rpc
        self.upgrade_rpc = upgrade_rpc
        self.odoo_url = odoo_url

    def with_task_name(self, task_name: str) -> Self:
        self.task_name = task_name
        return self

    def with_parent(self, parent: TripleFlag = TripleFlag.YES) -> Self:
        self.parent = parent
        return self

    def with_contract(self, contract: TripleFlag.YES) -> Self:
        self.contract = contract
        return self

    def with_show_sub(self) -> Self:
        self.show_sub = True
        return self

    def show_not_found(self) -> Self:
        self.hide_not_found = False
        return self

    def only_luck(self) -> Self:
        self.lucky = True
        return self

    def with_order_by_validity(self) -> Self:
        self.order_by_validity = True
        return self

    @abstractmethod
    def search(self) -> List[List[TableHeader] | List[dict]]:
        raise NotImplementedError

    @abstractmethod
    def _transform_to_rows(self, tasks: List[Task]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _display_task_list(self, rows: List[List[Any]]) -> List[List[TableHeader] | List[dict]]:
        raise NotImplementedError

    @abstractmethod
    def stats(self, group_by: List[str], union_wrapper: Optional[Callable]) -> List[List[Any]]:
        raise NotImplementedError
