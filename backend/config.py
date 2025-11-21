"""Application configuration helpers."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Tuple

from dotenv import load_dotenv

DEFAULT_EXTENSIONS = {"pptx", "docx", "xlsx"}


def _detect_paths() -> Tuple[Path, Path]:
    """Return (runtime_dir, resource_dir) for source or frozen builds."""
    if getattr(sys, "frozen", False):  # running from PyInstaller bundle
        exe_dir = Path(sys.executable).resolve().parent
        resource_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        return exe_dir, resource_dir
    base = Path(__file__).resolve().parent.parent
    return base, base


RUNTIME_DIR, RESOURCE_DIR = _detect_paths()


def _load_dotenv() -> None:
    """Load .env from runtime dir, falling back to bundled location."""
    for root in (RUNTIME_DIR, RESOURCE_DIR):
        env_path = root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return


_load_dotenv()


def _parse_list(value: str, default: Set[str]) -> Set[str]:
    if not value:
        return default
    return {item.strip() for item in value.split(",") if item.strip()}


@dataclass(frozen=True)
class Settings:
    """Container for runtime configuration values."""

    runtime_dir: Path = RUNTIME_DIR
    resource_dir: Path = RESOURCE_DIR
    secret_key: str = os.getenv("SECRET_KEY", "dev")
    upload_folder: Path = field(default_factory=lambda: RUNTIME_DIR / "uploads")
    output_folder: Path = field(default_factory=lambda: RUNTIME_DIR / "output")
    static_folder: Path = field(default_factory=lambda: RESOURCE_DIR / "frontend")
    max_content_length: int = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))
    allowed_extensions: Set[str] = field(
        default_factory=lambda: _parse_list(os.getenv("ALLOWED_EXTENSIONS", ""), DEFAULT_EXTENSIONS) | DEFAULT_EXTENSIONS
    )
    openrouter_api_base: str = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    default_model: str = os.getenv("DEFAULT_MODEL", "anthropic/claude-3.5-sonnet")
    
    # Authentication settings
    auth_base_url: str = os.getenv("AUTH_BASE_URL", "http://localhost:8000")
    gadget_id: str = os.getenv("GADGET_ID", "translateppt")
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "nexus_session")
    credential_db_url: str = os.getenv("CREDENTIAL_DB_URL", "http://localhost:3000")


settings = Settings()
