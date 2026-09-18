"""Configuration validation without exposing credential values."""

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    speech_endpoint: str = ""
    speech_api_key: str = field(default="", repr=False)
    speech_api_version: str = "2025-10-15"
    summary_endpoint: str = ""
    summary_api_key: str = field(default="", repr=False)
    summary_deployment: str = ""
    db_path: Path = Path("data/calls.sqlite3")
    temp_dir: Path = Path("tmp/audio")
    timeout_seconds: float = 120
    max_attempts: int = 3
    max_transcript_chars: int = 24000

    def with_ui_overrides(self, values: dict[str, str]) -> "Settings":
        """Nonblank session values override fallback settings, never the environment."""
        allowed = {"speech_endpoint", "speech_api_key", "summary_endpoint",
                   "summary_api_key", "summary_deployment"}
        overrides = {name: value.strip() for name, value in values.items()
                     if name in allowed and value.strip()}
        for name in ("speech_endpoint", "summary_endpoint"):
            if name in overrides:
                overrides[name] = overrides[name].rstrip("/")
        return replace(self, **overrides)

    @classmethod
    def from_env(cls, *, dotenv_path: str | Path = ".env") -> "Settings":
        load_dotenv(dotenv_path, override=False)
        def number(name, default, cast, low, high):
            try:
                value = cast(os.getenv(name, str(default)))
            except (ValueError, TypeError):
                raise ValueError(f"{name} must be a number.") from None
            if not low <= value <= high:
                raise ValueError(f"{name} must be between {low} and {high}.")
            return value
        return cls(
            speech_endpoint=os.getenv("AZURE_SPEECH_ENDPOINT", "").strip().rstrip("/"),
            speech_api_key=os.getenv("AZURE_SPEECH_API_KEY", "").strip(),
            speech_api_version=os.getenv("AZURE_SPEECH_API_VERSION", "2025-10-15").strip(),
            summary_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/"),
            summary_api_key=os.getenv("AZURE_OPENAI_API_KEY", "").strip(),
            summary_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip(),
            db_path=Path(os.getenv("CALL_INSIGHTS_DB_PATH", "data/calls.sqlite3")),
            temp_dir=Path(os.getenv("CALL_INSIGHTS_TEMP_DIR", "tmp/audio")),
            timeout_seconds=number("CALL_INSIGHTS_TIMEOUT_SECONDS", 120, float, 1, 300),
            max_attempts=number("CALL_INSIGHTS_MAX_ATTEMPTS", 3, int, 1, 5),
            max_transcript_chars=number("CALL_INSIGHTS_MAX_TRANSCRIPT_CHARS", 24000, int, 100, 100000),
        )

    def azure_errors(self) -> list[str]:
        errors = []
        for name, value in (
            ("AZURE_SPEECH_ENDPOINT", self.speech_endpoint),
            ("AZURE_SPEECH_API_KEY", self.speech_api_key),
            ("AZURE_OPENAI_ENDPOINT", self.summary_endpoint),
            ("AZURE_OPENAI_API_KEY", self.summary_api_key),
            ("AZURE_OPENAI_DEPLOYMENT", self.summary_deployment),
        ):
            if not value:
                errors.append(f"Set {name} in Azure settings, .env, or your environment.")
        for name, endpoint in (("AZURE_SPEECH_ENDPOINT", self.speech_endpoint),
                               ("AZURE_OPENAI_ENDPOINT", self.summary_endpoint)):
            if endpoint:
                try:
                    parsed = urlsplit(endpoint)
                    valid = parsed.scheme == "https" and bool(parsed.hostname) and not (
                        parsed.username or parsed.password or parsed.query or parsed.fragment
                    ) and parsed.path in ("", "/")
                except ValueError:
                    valid = False
                if not valid:
                    errors.append(f"{name} must be an HTTPS resource root URL, without a path or query.")
        return errors
