from odev.common.postgres import PostgresTable


class RRConfigStore(PostgresTable):
    name = "rr_config"
    _columns = {
        "key": "VARCHAR PRIMARY KEY",
        "value": "VARCHAR",
        "wrapper": "VARCHAR",
        "date": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }

    _default_keys = {
        "odoo_url": {"default": "www.odoo.com"},
        "odoo_database_name": {"default": "openerp"},
        "odoo_url_upg": {"default": "upgrade.odoo.com"},
        "odoo_database_name_upg": {"default": "odoo_upgrade"},
        "odoo_limit": {"wrapper": "int", "default": "700"},
        "odoo_task_domain": {
            "default": '["&", "&", "&", ["name", "ilike", "[rr]%"], ["user_ids", "=", False], ["stage_id", "in", [25525]], ["tag_ids", "in", [25106]]]',  # noqa: B950 [line too long]
            "wrapper": "eval",
        },
    }

    def clean_table(self):
        self.database.query(
            f"""
                DELETE FROM {self.name}
            """
        )

    def _create_default(self, key):
        key_data = self._default_keys.get(key, None)
        if key_data is None:
            raise Exception("No key in _default_keys")
        value = key_data.get("default", None)
        wrapper = key_data.get("wrapper", None)
        value_str = f"{value!r}" if value is not None else "NULL"
        wrapper_str = f"{wrapper!r}" if wrapper else "NULL"
        values = f"{key!r},{value_str},{wrapper_str}"

        self.database.query(
            f"""
                INSERT INTO {self.name}(key, value, wrapper)
                VALUES ({values}) ON CONFLICT DO NOTHING
            """
        )
        return eval(wrapper)(value) if wrapper is not None else value

    def _force_load_keys(self):
        for key in self._default_keys.keys():
            self.get(key)

    def prepare_database_table(self):
        super().prepare_database_table()
        self._force_load_keys()

    def set(self, key, value, wrapper=None):
        wrapper_query = None
        if not value:
            value = "NULL"
        elif not isinstance(value, str):
            value = f"{str(value)!r}"
        if wrapper:
            try:
                eval(wrapper)(value)
                wrapper_query = f"{str(wrapper)!r}"
            except Exception:
                raise Exception(f"Error in value {value}, the wrapper: {wrapper} looks not valid")
        else:
            wrapper_query = "NULL"

        self.database.query(
            f"""
            UPDATE {self.name}
               SET value={value}, wrapper={wrapper_query}
            WHERE key={key!r}
            """
        )

    def get(self, key):
        result = self.database.query(
            f"""
            SELECT value, wrapper
              FROM {self.name}
             WHERE key={key!r}
             LIMIT 1
            """
        )
        if not len(result):
            return self._create_default(key)
        value, wrapper = result[0]
        if wrapper and value is not None:
            value = eval(wrapper)(value)
        return value

    def get_row(self, key):
        return self.database.query(
            f"""
            SELECT key, value, wrapper
              FROM {self.name}
             WHERE key={key!r}
             LIMIT 1
            """
        )

    def get_all(self):
        return self.database.query(
            f"""
            SELECT key, value, wrapper
              FROM {self.name}
            """
        )
