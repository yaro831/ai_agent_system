
# config/settings.py

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4-turbo")
MAX_TOKENS_PER_REQUEST = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4096"))

# Database Configuration
DB_URI = os.getenv("DB_URI", "mongodb://localhost:27017/ai_agents")
DB_NAME = os.getenv("DB_NAME", "ai_agents")

# System Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
AGENT_CONFIG_PATH = os.getenv("AGENT_CONFIG_PATH", "config/agent_config.json")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "development_secret_key")

# Protocol Settings
PROTOCOL_VERSION = "1.0"
DEFAULT_TIMEOUT = 30  # seconds

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Agent Settings
DEFAULT_AGENT_PARAMS: Dict[str, Any] = {
    "temperature": 0.7,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "max_tokens": 1000
}

# Function to get a specific agent's configuration
def get_agent_config(agent_type: str) -> Optional[Dict[str, Any]]:
    import json
    import os
    
    config_path = AGENT_CONFIG_PATH
    
    if not os.path.exists(config_path):
        return None
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config.get('agents', {}).get(agent_type)
