from pydantic_settings import SettingsConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_root: str
    db_user_admin: str
    db_password_admin: str
    db_user: str
    db_password: str
    db_name: str
    db_host: str
    db_port: int

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
