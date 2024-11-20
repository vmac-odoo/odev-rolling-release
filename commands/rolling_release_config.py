from odev.common import args
from odev.common.commands import Command
from odev.common.console import TableHeader
from odev.common.logging import logging


logger = logging.getLogger(__name__)


class RollingReleaseConfig(Command):

    _name = "rolling-release-config"
    _aliases = ["rr-config"]

    action_clean = args.Flag(
        name="clean",
        aliases=["-c", "--clean"],
        description="Clean all configurations.",
    )
    action_show_all = args.Flag(
        name="show",
        aliases=["-s", "--show"],
        description="Show all configurations.",
    )
    action_update_key = args.String(
        name="update_key",
        aliases=["-u", "--update"],
        description="Update value and wrapper in the database.",
    )

    def _get_conf_titles(self):
        return [
            TableHeader("Key", style="bold color.purple"),
            TableHeader("Value"),
            TableHeader("Wrapper"),
        ]

    def clean(self):
        confirm: bool = self.console.confirm(
            "Are you sure you want to delete all rr configurations?",
            default=True,
        )
        if confirm:
            logger.info("Deleting rr configurations.")
            self.store.rr_config.clean_table()

    def show_all(self):
        rows = self.store.rr_config.get_all()
        self.table(self._get_conf_titles(), rows)

    def update_key(self, key):
        row = self.store.rr_config.get_row(key)
        self.table(self._get_conf_titles(), row)
        confirm: bool = self.console.confirm(
            "Are you sure you want to update it?",
            default=True,
        )
        if confirm:
            value = self.console.text("Give the new value: ")
            wrapper = self.console.text("Give the new wrapper: ")
            self.store.rr_config.set(key, value, wrapper)

    def run(self):
        if self.args.clean:
            self.clean()
        if self.args.show:
            self.show_all()
        if update_key := self.args.update_key:
            self.update_key(update_key)
