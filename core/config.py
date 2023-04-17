from pydantic import BaseSettings


class Settings(BaseSettings):
    """Настройки проекта."""

    database_url: str = 'sqlite+aiosqlite:///./users_images.db'
    bot_token: str = 'BOT_TOKEN'

    class Config:
        env_file = '.env'


settings = Settings()
