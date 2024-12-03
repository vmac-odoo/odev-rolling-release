from odev.plugins.odev_rolling_release.api.dtos.Subscription import Subscription
from odev.plugins.odev_rolling_release.api.services.service_abstract import Service


class SaleOrderService(Service[Subscription]):
    model_name = "sale.order"
    model_class = Subscription
