from odev.common import args, progress
from odev.common.commands import Command
from odev.common.connectors.rpc import RpcConnector
from odev.common.databases.remote import RemoteDatabase
from odev.common.logging import logging

from odev.plugins.odev_rolling_release.api.strategy.bs4_strategy import Bs4Strategy
from odev.plugins.odev_rolling_release.api.strategy.strategy_abstract import Strategy
from odev.plugins.odev_rolling_release.api.strategy.title_strategy import TitleStrategy
from odev.plugins.odev_rolling_release.utils.utils import TripleFlag, group_by_record_exists


logger = logging.getLogger(__name__)


class RollingRelease(Command):

    _name = "rolling-release"
    _aliases = ["rr"]
    rolling_strategy: Strategy

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

    def _set_strategy(self) -> Strategy:
        if self.args.bs4:
            logger.info("[EXPERIMENTAL] This strategy could give you a different result vs standard one.")
            self.rolling_strategy = Bs4Strategy
        else:
            self.rolling_strategy = TitleStrategy

    def _set_single_configs(self) -> None:
        # conditional / callable / log
        single_confs = [
            (
                self.args.ghosts,
                self.rolling.show_not_found,
                "Do you want ghosts?",
            ),
            (self.args.lucky, self.rolling.only_luck, "You feel so lucky?"),
            (
                self.args.explicit_contract,
                self.rolling.with_show_sub,
                "I will show u all...",
            ),
        ]

        for conditional, func, log in single_confs:
            if conditional:
                logger.info(log)
                func()

    def _set_double_configs(self) -> None:
        # title / arg pos / arg neg / callable
        double_confs = [
            (
                "Has contract:",
                self.args.contract,
                self.args.no_contract,
                self.rolling.with_contract,
            ),
            (
                "Has parent:",
                self.args.parent,
                self.args.no_parent,
                self.rolling.with_parent,
            ),
        ]
        for title, positive_val, negative_val, func in double_confs:
            if positive_val:
                logger.info(f"{title} {TripleFlag.YES.value}")
                func(TripleFlag.YES)
            elif negative_val:
                logger.info(f"{title} {TripleFlag.NO.value}")
                func(TripleFlag.NO)

    def _get_rpc_connection(self, url, database) -> RpcConnector:
        return RpcConnector(RemoteDatabase(url, database))

    def _setup_run_conf(self):
        logger.info("Loading Configuration")
        self._set_strategy()
        rr_config = self.store.rr_config

        odoo_rpc = self._get_rpc_connection(rr_config.get("odoo_url"), rr_config.get("odoo_database_name"))
        upgrade_rpc = None
        if self.args.upgrade:
            logger.info("UP!")
            upgrade_rpc = self._get_rpc_connection(
                rr_config.get("odoo_url_upg"), rr_config.get("odoo_database_name_upg")
            )
        self.rolling = self.rolling_strategy(
            rr_config.get("odoo_task_domain"),
            rr_config.get("odoo_limit"),
            odoo_rpc,
            upgrade_rpc,
            rr_config.get("odoo_url"),
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
