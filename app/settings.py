import os
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)


class Settings:
    HOST: str = os.getenv("HOST")
    PORT: int = int(os.getenv("PORT"))
    
    APP_VERSION = "0.1.0"
