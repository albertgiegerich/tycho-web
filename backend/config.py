from pydantic_settings import SettingsConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_root: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
