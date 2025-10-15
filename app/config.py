# FILE: app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict


class Settings(BaseSettings):
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

    # --- File Paths (for persistent disk) ---
    ITEMS_PATH: str = "/data/items.json"
    FAISS_INDEX_PATH: str = "/data/faiss.index"

    # --- Search Algorithm Tuning ---
    CATEGORY_BOOST: float = 0.1
    NAME_KEYWORD_BOOST: float = 0.1
    DESC_KEYWORD_BOOST: float = 0.05
    SERVICE_NAME_WEIGHT: float = 0.6
    CATEGORY_NAME_WEIGHT: float = 0.2
    SERVICE_DESCRIPTION_WEIGHT: float = 0.2

    # --- Relevance Logic Thresholds ---
    DID_YOU_MEAN_THRESHOLD: float = 0.3

    # --- Query Expansion ---
    SYNONYM_MAP: Dict[str, str] = {
        "marriage": "wedding", "shadi": "wedding", "event": "event planning",
        "party": "event planning", "function": "event planning", "organizer": "event planning",
        "photos": "photography", "pics": "photography", "photographer": "photography",
        "video": "videography", "movie": "videography", "film": "videography",
        "food": "catering", "khana": "catering", "dinner": "catering", "lunch": "catering",
        "dj": "entertainment", "music": "entertainment", "band": "entertainment",
        "singer": "entertainment", "dance": "entertainment",
        "venue": "venues", "place": "venues", "hall": "venues", "hotel": "venues",
        "resort": "venues", "location": "venues",
        "makeup": "beauty & makeup", "bridal": "beauty & makeup", "dress": "fashion & attire",
        "outfit": "fashion & attire", "lehenga": "fashion & attire", "attire": "fashion & attire",
        "decor": "decorations", "decoration": "decorations", "sajawat": "decorations",
        "lights": "production (sound & lights)", "sound": "production (sound & lights)",
        "flowers": "florists", "florist": "florists",
        "gifts": "gifting", "favors": "gifting", "invites": "invitations", "cards": "invitations",
    }

    # --- Predefined Data ---
    PREDEFINED_CATEGORIES: List[str] = [
        "Catering", "Decorations", "Photography", "Videography",
        "Beauty & Makeup", "Fashion & Attire", "Invitations", "Venues",
        "Entertainment", "Music Bands", "DJs", "Travel", "Transport",
        "Event Planning", "Florists", "Production (Sound & Lights)",
        "Fireworks", "Mehndi Artists", "Gifting", "Jewellery"
    ]


settings = Settings()
