from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env from backend directory so POE_API_KEY is in os.environ before Settings() runs
_env_dir = Path(__file__).resolve().parent.parent
_env_path = _env_dir / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # fallback: .env in cwd


class Settings(BaseSettings):
    # Poe API only: https://poe.com/api_key
    poe_api_key: str = ""
    poe_model: str = "Claude-Sonnet-4"  # e.g. Claude-Sonnet-4, GPT-4o
    database_url: str = "sqlite+aiosqlite:///./dailycare.db"

    # Triage thresholds (heart failure context)
    vitals_sbp_high: int = 180
    vitals_sbp_low: int = 90
    vitals_dbp_high: int = 110
    vitals_dbp_low: int = 60
    vitals_hr_high: int = 120
    vitals_hr_low: int = 50
    vitals_weight_gain_kg_alert: float = 2.0
    vitals_temp_high: float = 38.0
    vitals_temp_low: float = 35.0

    model_config = {"env_file": _env_path if _env_path.exists() else ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
