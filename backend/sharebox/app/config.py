from __future__ import annotations

import json
import os
import socket
import sys
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def default_app_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ShareBox"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ShareBox"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "sharebox"


def default_shared_folder() -> Path:
    return Path.home() / "ShareBox"


class AppConfig(BaseModel):
    shared_folder: str = Field(default_factory=lambda: str(default_shared_folder()))
    port: int = 8765
    host_name: str = Field(default_factory=lambda: socket.gethostname() or "ShareBox")
    launch_at_startup: bool = False
    bind_host: str = "0.0.0.0"
    installation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pairing_ttl_seconds: int = 300
    debug: bool = False
    # Serve the LAN over HTTPS with a self-signed certificate. Off by default:
    # it costs the user a one-time browser warning per device.
    use_https: bool = False
    # Loopback-only plain-HTTP port for the Control Center window, used when
    # HTTPS is on so the WebView never has to trust a self-signed certificate.
    # 0 means "port + 1".
    control_port: int = 0


class ConfigStore:
    def __init__(self, app_data_dir: Path | None = None) -> None:
        self.app_data_dir = app_data_dir or default_app_data_dir()
        self.config_path = self.app_data_dir / "config.json"
        self.db_path = self.app_data_dir / "sharebox.db"
        self.log_dir = self.app_data_dir / "logs"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load()

    @property
    def config(self) -> AppConfig:
        return self._config

    def _load(self) -> AppConfig:
        if not self.config_path.exists():
            cfg = AppConfig()
            self._write(cfg)
            return cfg
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(data)

    def _write(self, cfg: AppConfig) -> None:
        self.config_path.write_text(
            cfg.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def update(self, **kwargs: Any) -> AppConfig:
        data = self._config.model_dump()
        data.update(kwargs)
        self._config = AppConfig.model_validate(data)
        self._write(self._config)
        return self._config

    def effective_control_port(self) -> int:
        return self._config.control_port or self._config.port + 1

    def shared_folder_path(self) -> Path:
        path = Path(self._config.shared_folder)
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()
