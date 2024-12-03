from odev.plugins.odev_rolling_release.api.dtos.Database import Database
from odev.plugins.odev_rolling_release.api.services.service_abstract import Service


class DatabaseService(Service[Database]):
    model_name = "openerp.enterprise.database"
    model_class = Database
