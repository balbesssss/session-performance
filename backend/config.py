from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()