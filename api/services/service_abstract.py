from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from typing_extensions import Self

from odev.common.connectors.rpc import Model, RpcConnector

from odev.plugins.odev_rolling_release.utils.osv import AND


T = TypeVar("T")


class Service(Generic[T]):

    # to avoid TypeVar issue
    model_class: Optional[Type[T]] = None

    odoo_rpc: RpcConnector
    upgrade_rpc: Optional[RpcConnector]
    model_name: str = None
    domain: List[Any]
    fields: List[str]
    limit: int

    def __init__(self, odoo_rpc: RpcConnector) -> None:
        self.odoo_rpc = odoo_rpc
        self.domain = []
        self.fields = ["id"]

    def _get_model(self, model: str) -> Model:
        return Model(self.odoo_rpc, model)

    def with_domain(self, domain: List[Any]) -> Self:
        self.domain = AND([self.domain, domain]) if len(self.domain) else domain
        return self

    def with_fields(self, fields: List[str]) -> Self:
        self.fields.extend(fields)
        return self

    def with_limit(self, limit: int) -> Self:
        self.limit = limit
        return self

    def clean_for_model(self, response: List[dict]) -> List[dict]:
        # This could be override to allow response be adapted to object
        return response

    def _add_response(self, response: dict) -> dict:
        # This could be override to allow add more custom data
        return response

    def fetch(self, **kwargs) -> List[T]:
        if not self.model_name:
            raise ValueError("No model defined on Service")

        if not self.model_class:
            raise ValueError("No concrete model class specified")

        response: List[dict] = self.clean_for_model(
            self._get_model(self.model_name).search_read(
                domain=self.domain, fields=self.fields, limit=self.limit, **kwargs
            )
        )
        return [self.model_class(**self._add_response(row)) for row in response]

    def _clean_stats(self, datalist: List[dict], union_wrapper: Optional[Callable] = None):
        return datalist if not callable(union_wrapper) else union_wrapper(datalist)

    def fetch_group(self, group_by: List[str], union_wrapper: Optional[Callable] = None):
        response: List[dict] = self._get_model(self.model_name).read_group(
            domain=self.domain,
            groupby=group_by,
            limit=self.limit,
        )
        return self._clean_stats(response, union_wrapper)
