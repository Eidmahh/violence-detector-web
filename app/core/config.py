from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Violence Detector"
    DATABASE_URL: str = "sqlite:///./violence_db.sqlite"
    JWT_SECRET: str
    TWOFA_ISSUER: str = "ViolenceDetector"
    CAMERA_INDICES: list[int] = [0]
    SEQ_LEN: int = 16
    MAX_PEOPLE: int = 5
    WARNING_THRESHOLD: float = 0.3
    URGENT_THRESHOLD: float = 0.7
    SMOOTHING_WINDOW: int = 5
    NORMAL_DIR: str = "./data/normal"
    VIOLENT_DIR: str = "./data/violent"
    MODEL_PATH: str = "./model/model.pth"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
