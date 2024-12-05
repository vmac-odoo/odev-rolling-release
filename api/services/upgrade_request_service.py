from itertools import groupby
from typing import List

from odev.plugins.odev_rolling_release.api.dtos.UpgradeRequest import UpgradeRequest
from odev.plugins.odev_rolling_release.api.services.service_abstract import Service


class UpgradeRequestService(Service[UpgradeRequest]):
    model_name = "upgrade.request"
    model_class = UpgradeRequest
    is_upgrade_model = True

    def clean_for_model(self, response: List[dict]) -> List[dict]:
        response = super().clean_for_model(response)
        response.sort(key=lambda r: r["db_uuid"])
        requests = []
        for _, group in groupby(response, lambda r: r["db_uuid"]):
            requests.append(max(group, key=lambda x: x["id"]))
        return requests
