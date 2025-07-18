import os
from datetime import timedelta

class Config:
    """
    Base configuration class.
    """
    # Flask settings
    RUNPOD_ID = os.environ.get("RUNPOD_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")

    # JWT settings
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Database settings
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # OpenAI settings
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # Blockchain settings
    GANACHE_URL = os.environ.get("GANACHE_URL", "http://ganache:8545")

    # CORS settings
    CORS_ORIGINS = ["*"]  # Allow all origins

    # Logging settings
    LOG_LEVEL = "INFO"

    @classmethod
    def get_config(cls):
        """
        Get the configuration as a dictionary.

        Returns:
            dict: Configuration dictionary.
        """
        return {
            "SECRET_KEY": cls.SECRET_KEY,
            "JWT_SECRET_KEY": cls.JWT_SECRET_KEY,
            "JWT_ACCESS_TOKEN_EXPIRES": cls.JWT_ACCESS_TOKEN_EXPIRES,
            "DATABASE_URL": cls.DATABASE_URL,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "GANACHE_URL": cls.GANACHE_URL,
            "CORS_ORIGINS": cls.CORS_ORIGINS,
            "LOG_LEVEL": cls.LOG_LEVEL,
            "RUNPOD_ID": cls.RUNPOD_ID,
        }
