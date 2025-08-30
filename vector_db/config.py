"""Configuration management - simplified version."""

# Re-export the simplified config from src/config.py
from src.config import Config, get_config, reload_config

__all__ = ["Config", "get_config", "reload_config"]