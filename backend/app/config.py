import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://eventus_user:eventus_password@localhost:5432/eventus_db")
    GIGACHAT_CLIENT_ID: str = os.getenv("GIGACHAT_CLIENT_ID", "")
    GIGACHAT_SECRET: str = os.getenv("GIGACHAT_SECRET", "")
    GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    VK_ACCESS_TOKEN: str = os.getenv("VK_ACCESS_TOKEN", "")
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

settings = Settings()