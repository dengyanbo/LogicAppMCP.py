"""Minimal stub of pydantic_settings for testing configuration without dependency."""

class BaseSettings:
    model_config = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class SettingsConfigDict(dict):
    pass
