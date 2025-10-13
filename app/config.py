# FILE: app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Database Settings ---
    MONGODB_URL: str
    DATABASE_NAME: str = "anandutsav"
    COLLECTION_NAME: str = "services"

    # --- Machine Learning Model ---
    MODEL_NAME: str = "all-mpnet-base-v2"

    # --- File Paths ---
    EMBEDDINGS_PATH: str = "data/embeddings.npy"
    ITEMS_PATH: str = "data/items.json"
    FAISS_INDEX_PATH: str = "data/faiss.index"

    # --- Search Algorithm ---
    CATEGORY_BOOST: float = 0.1
    KEYWORD_BOOST: float = 0.05

    # --- Background Tasks ---
    REFRESH_SCHEDULE_SECONDS: int = 3600

    # --- Predefined Data ---
    PREDEFINED_CATEGORIES: List[str] = [
        "Catering", "Decorations", "Photography", "Videography",
        "Beauty & Makeup", "Fashion & Attire", "Invitations", "Venues",
        "Entertainment", "Music Bands", "DJs", "Travel", "Transport",
        "Event Planning", "Florists", "Production (Sound & Lights)",
        "Fireworks", "Mehndi Artists", "Gifting", "Jewellery"
    ]


settings = Settings()
