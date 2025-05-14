# app/core/config.py

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ViolenceDetectorWeb"

    # Database
    DATABASE_URL: str  # e.g. postgresql://user:pass@localhost/dbname

    # JWT / Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # one week

    # 2FA (TOTP)
    TWOFA_ISSUER: str = "ViolenceDetector"

    # Detector configuration
    CAMERA_INDICES: List[int] = [0]
    SEQ_LEN: int = 1
    MAX_PEOPLE: int = 2
    SMOOTHING_WINDOW: int = 5

    # Paths (relative to project root)
    NORMAL_DIR: str = "data/non_violence"
    VIOLENT_DIR: str = "data/violence"
    MODEL_PATH: str = "models/violence_transformer_model"
    FEATURES_PATH: str = "data/extracted_features2.pkl"

    # Detection thresholds
    WARNING_THRESHOLD: float = 0.55
    URGENT_THRESHOLD: float = 0.65

    # tell Pydantic where to load .env from
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
