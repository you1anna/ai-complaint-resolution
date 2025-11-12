"""
Configuration management for the complaint resolution system
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    # API Configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./complaint_resolution.db")

    # Application
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_human_review: bool = os.getenv("ENABLE_HUMAN_REVIEW", "true").lower() == "true"
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))

    # Paths
    project_root: Path = Path(__file__).parent.parent
    config_path: Path = project_root / "config" / "config.yaml"
    data_path: Path = project_root / "data"

    class Config:
        env_file = ".env"


def load_yaml_config(config_path: Path) -> Dict:
    """Load YAML configuration file"""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# Global settings instance
settings = Settings()

# Load YAML config
try:
    yaml_config = load_yaml_config(settings.config_path)
except FileNotFoundError:
    # Fallback defaults if config.yaml doesn't exist
    yaml_config = {
        "supported_languages": ["en", "it", "de", "fr", "es"],
        "complaint_categories": [
            "claim_rejection", "service_quality", "policy_interpretation",
            "medical_coverage", "trip_cancellation", "baggage_loss",
            "travel_delay", "communication_issue"
        ],
        "sla_timelines": {"international": 15, "uk_domestic": 56},
        "human_review": {"confidence_threshold": 0.85}
    }

# Export commonly used configs
SUPPORTED_LANGUAGES: List[str] = yaml_config.get("supported_languages", ["en", "it"])
COMPLAINT_CATEGORIES: List[str] = yaml_config.get("complaint_categories", [])
SLA_TIMELINES: Dict[str, int] = yaml_config.get("sla_timelines", {})
URGENCY_INDICATORS: Dict = yaml_config.get("urgency_indicators", {})
