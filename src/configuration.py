from enum import Enum

from pydantic import BaseModel, Field, computed_field


class LoadType(str, Enum):
    incremental_load = "incremental_load"
    full_load = "full_load"


class Connection(BaseModel):
    server_url: str
    user_name: str
    password: str = Field(alias="#password")
    db_profile: str
    use_windows_authentication: bool = False
    language_id: str = "en"


class Configuration(BaseModel):
    acknowledge: bool = False
    connection: Connection
    batch_size: int = 1000
    requests_per_minute: int = 30
    debug: bool = False

    entity: str
    table_name: str = ""
    load_type: LoadType = Field(default=LoadType.incremental_load)

    @computed_field
    @property
    def is_incremental(self) -> bool:
        return self.load_type == LoadType.incremental_load

    @property
    def output_table_name(self) -> str:
        return self.table_name or self.entity
