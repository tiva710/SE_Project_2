from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    class Config:
        env_file = ".env"

settings = Settings()
