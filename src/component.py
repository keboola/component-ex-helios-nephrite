"""
Helios Nephrite Component - Extracts data from Helios Nephrite ERP API.
"""

import json
import logging
from datetime import datetime, timezone

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

from client import HeliosNephriteClient
from configuration import Configuration
from writer import TableWriter

NESTED_FIELDS = {"addresses", "customAttributes", "customRelations", "categories", "manufacturers", "images"}


class Component(ComponentBase):
    def __init__(self):
        super().__init__()
        self.cfg: Configuration | None = None
        self.state: dict = {}
        self.client: HeliosNephriteClient | None = None

    def run(self):
        self.cfg = Configuration(**self.configuration.parameters)
        self.state = self.get_state_file() or {"endpoints": {}}

        self.client = HeliosNephriteClient(
            server_url=self.cfg.connection.server_url,
            user_name=self.cfg.connection.user_name,
            password=self.cfg.connection.password,
            db_profile=self.cfg.connection.db_profile,
            use_windows_auth=self.cfg.connection.use_windows_authentication,
            language_id=self.cfg.connection.language_id,
            requests_per_minute=self.cfg.requests_per_minute,
        )

        try:
            self.client.login()
            logging.info("Successfully authenticated to Helios Nephrite")

            self._process_endpoint()

            self.state["last_run"] = datetime.now(timezone.utc).isoformat()
            self.write_state_file(self.state)
            logging.info("State file updated successfully")

        finally:
            if self.client:
                self.client.logout()

    def _process_endpoint(self) -> None:
        entity = self.cfg.entity
        table_name = self.cfg.output_table_name
        is_incremental = self.cfg.is_incremental

        logging.info(f"Processing entity: {entity} -> table: {table_name}")

        last_timestamp = None
        if is_incremental:
            entity_state = self.state.get("endpoints", {}).get(entity, {})
            last_timestamp = entity_state.get("last_timestamp")
            if last_timestamp is not None:
                logging.info(f"Resuming incremental load from timestamp: {last_timestamp}")

        writers = self._init_writers(table_name, is_incremental)

        max_timestamp = last_timestamp
        total_records = 0

        try:
            for batch in self.client.get_entities(entity, last_timestamp, self.cfg.batch_size):
                for record in batch:
                    main_record, child_records = self._split_record(record)
                    main_record = self._expand_custom_attributes(main_record, record.get("customAttributes", []))
                    writers["main"].writerow(main_record)

                    record_id = record.get("id")
                    for child_type, child_data in child_records.items():
                        if child_type in writers and child_data:
                            for child in child_data:
                                child["parent_id"] = record_id
                                writers[child_type].writerow(child)

                    if is_incremental and record.get("timestamp") is not None:
                        current_ts = record["timestamp"]
                        if max_timestamp is None or current_ts > max_timestamp:
                            max_timestamp = current_ts

                total_records += len(batch)

            logging.info(f"Completed extraction: {total_records} records from {entity}")

            self.state.setdefault("endpoints", {})[entity] = {
                "last_timestamp": max_timestamp,
                "last_run_iso": datetime.now(timezone.utc).isoformat(),
                "records_extracted": total_records,
            }

        finally:
            for writer in writers.values():
                writer.close()

    def _split_record(self, record: dict) -> tuple[dict, dict[str, list]]:
        """Split record into main (scalar) fields and child (array) fields."""
        main_record = {}
        child_records = {}

        for key, value in record.items():
            if key in NESTED_FIELDS and isinstance(value, list):
                child_records[key] = value
            elif isinstance(value, dict):
                for nested_key, nested_val in value.items():
                    if isinstance(nested_val, (dict, list)):
                        continue
                    main_record[f"{key}_{nested_key}"] = nested_val
            elif isinstance(value, list):
                main_record[key] = json.dumps(value) if value else None
            else:
                main_record[key] = value

        return main_record, child_records

    def _expand_custom_attributes(self, record: dict, custom_attrs: list) -> dict:
        """Expand customAttributes array to individual columns (custom_{name} = value)."""
        for attr in custom_attrs:
            attr_name = attr.get("name", "")
            if attr_name:
                safe_name = attr_name.lower().replace(" ", "_").replace("-", "_")
                safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
                if safe_name:
                    record[f"custom_{safe_name}"] = attr.get("value", "")
        return record

    def _init_writers(self, table_name: str, incremental: bool) -> dict[str, TableWriter]:
        writers = {}
        main_table = self.create_out_table_definition(
            f"{table_name}.csv",
            incremental=incremental,
            primary_key=["id"],
        )
        self.write_manifest(main_table)
        writers["main"] = TableWriter(main_table.full_path)

        for child_type in NESTED_FIELDS:
            child_table = self.create_out_table_definition(
                f"{table_name}_{child_type}.csv",
                incremental=incremental,
                primary_key=["parent_id", "id"],
            )
            self.write_manifest(child_table)
            writers[child_type] = TableWriter(child_table.full_path, lazy=True)

        return writers


if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
