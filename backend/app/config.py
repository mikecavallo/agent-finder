from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    linkedin_email: str
    linkedin_password: str
    secret_key: str
    access_token_expire_minutes: int = 30

    # Email Settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    sender_email: str
    
    class Config:
        env_file = ".env"

settings = Settings()
