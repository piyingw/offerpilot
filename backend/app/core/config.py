from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "OfferPilot API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # 生产环境务必通过 .env 覆盖为随机长字符串
    SECRET_KEY: str = "dev-secret-do-not-use-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 设置 DATABASE_URL 可整体覆盖下面的 MySQL 单项配置（测试环境用 SQLite）
    DATABASE_URL: str | None = None
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "offerpilot"
    MYSQL_PASSWORD: str = "offerpilot"
    MYSQL_DB: str = "offerpilot"

    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # LLM 配置：provider 预设了 base_url 和默认模型，均可单独覆盖
    LLM_PROVIDER: str = "glm"  # glm | deepseek | qwen
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    UPLOAD_DIR: str = "uploads"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
