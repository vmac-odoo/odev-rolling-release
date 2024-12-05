from typing_extensions import Self

from odev.plugins.odev_rolling_release.api.dtos.Task import Task
from odev.plugins.odev_rolling_release.api.services.service_abstract import Service


class TaskService(Service[Task]):
    model_name = "project.task"
    model_class = Task

    show_sub: bool = False
    upgrade_mode: bool = False

    def with_sub(self) -> Self:
        self.show_sub = True
        return self

    def with_upgrade_mode(self) -> Self:
        self.upgrade_mode = True
        return self

    def _add_response(self, response: dict) -> dict:
        response = super()._add_response(response)
        response["show_sub"] = self.show_sub
        response["upgrade_mode"] = self.upgrade_mode
        return response
