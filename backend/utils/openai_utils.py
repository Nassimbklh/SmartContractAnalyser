"""
OpenAI API utilities
"""

import os
import openai
from ..config import Config

def initialize_openai():
    """
    Initialize the OpenAI API with the API key from the environment variables.
    """
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key is not set in the environment variables.")
    
    openai.api_key = api_key
    return api_key

# Initialize OpenAI API when this module is imported
initialize_openai()