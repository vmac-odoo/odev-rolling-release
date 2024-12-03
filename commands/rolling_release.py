from odev.common import args, progress
from odev.common.commands import Command
from odev.common.logging import logging

from odev.plugins.odev_rolling_release.api.mixins.mixins import RollingMixing
from odev.plugins.odev_rolling_release.api.strategy.by_bs4 import RollingByBs4Strategy
from odev.plugins.odev_rolling_release.api.strategy.by_title import RollingByTitleStrategy
from odev.plugins.odev_rolling_release.utils.utils import TripleFlag, group_by_record_exists


logger = logging.getLogger(__name__)


class RollingRelease(Command):

    _name = "rolling-release"
    _aliases = ["rr"]
    rolling_strategy: RollingMixing

    task_name = args.String(
        name="task",
        aliases=["-t", "--task"],
        description="Search task by ilike name.",
    )

    action_bs4 = args.Flag(
        name="bs4",
        aliases=["-bs4", "--bs4"],
        description="[EXPERIMENTAL] Use description bs4 strategy instead of name by default.",
    )

    action_stats = args.Flag(
        name="stats",
        aliases=["-s", "--stats"],
        description="Get stats of databases.",
    )

    action_contract = args.Flag(
        name="contract",
        aliases=["-c", "--contract"],
        description="Only search with contract.",
    )

    action_no_contract = args.Flag(
        name="no_contract",
        aliases=["-nc", "--no-contract"],
        description="Only search with no contract.",
    )

    action_parent = args.Flag(
        name="parent",
        aliases=["-p", "--parent"],
        description="Only search with parent.",
    )

    action_no_parent = args.Flag(
        name="no_parent",
        aliases=["-np", "--no-parent"],
        description="Only search with no parent.",
    )

    action_ghosts = args.Flag(
        name="ghosts",
        aliases=["-g", "--ghosts"],
        description="Show not found databases, a database couldn't be found because a filter or is a dropped database.",
    )

    action_explicit_contract = args.Flag(
        name="explicit_contract",
        aliases=["-ex", "--explicit"],
        description="Show the real contract.",
    )

    action_lucky = args.Flag(
        name="lucky",
        aliases=["-l", "--lucky"],
        description="I don't care, just give me sth.",
    )

    action_upgrade = args.Flag(
        name="upgrade",
        aliases=["-u", "--upgrade"],
        description="[EXPERIMENTAL] Upgrade data.",
    )

    def _set_strategy(self) -> RollingMixing:
        if self.args.bs4:
            logger.info("[EXPERIMENTAL] This strategy could give you a different result vs standard one.")
            self.rolling_strategy = RollingByBs4Strategy
        else:
            self.rolling_strategy = RollingByTitleStrategy

    def _set_single_configs(self) -> None:
        single_confs = [
            (self.args.ghosts, "hide_not_found", False, "Do you want ghosts?"),
            (self.args.lucky, "lucky", True, "You feel so lucky?"),
            (self.args.explicit_contract, "show_sub", True, "I will show u all..."),
        ]

        for args_value, attr, attr_value, log in single_confs:
            if args_value:
                logger.info(log)
                setattr(self.rolling, attr, attr_value)

    def _set_double_configs(self) -> None:
        double_confs = [
            (
                "Has contract:",
                self.args.contract,
                self.args.no_contract,
                "with_contract",
            ),
            ("Has parent:", self.args.parent, self.args.no_parent, "with_parent"),
        ]
        for title, positive_val, negative_val, attr in double_confs:
            if positive_val:
                logger.info(f"{title} {TripleFlag.YES.value}")
                setattr(self.rolling, attr, TripleFlag.YES)
            elif negative_val:
                logger.info(f"{title} {TripleFlag.NO.value}")
                setattr(self.rolling, attr, TripleFlag.NO)

    def _setup_run_conf(self):
        logger.info("Loading Configuration")
        self._set_strategy()
        rr_config = self.store.rr_config
        if self.args.upgrade:
            logger.info("UP!")
        self.rolling = self.rolling_strategy(
            rr_config.get("odoo_url"),
            rr_config.get("odoo_database_name"),
            rr_config.get("odoo_limit"),
            rr_config.get("odoo_task_domain"),
            self.args.upgrade,
            rr_config.get("odoo_url_upg"),
            rr_config.get("odoo_database_name_upg"),
        )

        self._set_double_configs()
        self._set_single_configs()

        if task := self.args.task:
            logger.info(f"Searching by name: {task}")
            self.rolling.task_name = task

    def run(self):
        self._setup_run_conf()
        if self.args.stats:
            self.list_all_stats()
        else:
            self.list_databases()

    def list_databases(self):
        with progress.spinner("Loading RR Tickets..."):
            self.table(*self.rolling.search())

    def list_all_stats(self):
        with progress.spinner("Loading RR Stats..."):
            group_by_list = [
                ["version", False],
                [
                    "parent_id",
                    lambda x: group_by_record_exists(x, "parent_id"),
                ],
                [
                    "subscription_id",
                    lambda x: group_by_record_exists(x, "subscription_id"),
                ],
            ]
            if self.args.upgrade:
                group_by_list.append(
                    [
                        "subscription_id",
                        lambda x: group_by_record_exists(x, "subscription_id"),
                    ]
                )
            for group_by, wrapper in group_by_list:
                logger.info(f"Stats by {group_by}")
                self.table(*self.rolling.stats([group_by], wrapper))
