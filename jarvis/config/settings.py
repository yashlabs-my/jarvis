"""
Jarvis Configuration Module
Centralized configuration management for the Jarvis AI assistant.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Centralized configuration manager for Jarvis."""
    
    # API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Wake Word Configuration
    WAKE_WORD: str = "jarvis"
    WAKE_WORD_SENSITIVITY: float = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.7"))
    
    # TTS Configuration
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AndrewMultilingualNeural")
    TTS_RATE: str = os.getenv("TTS_RATE", "+20%")
    TTS_PITCH: str = os.getenv("TTS_PITCH", "+10Hz")
    
    # STT Configuration
    WHISPER_MODEL: str = "base.en"
    SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    
    # Memory Configuration
    DATABASE_PATH: Path = Path(__file__).parent.parent / "memory" / "jarvis.db"
    
    # Performance Configuration
    MAX_CONVERSATION_HISTORY: int = 20
    RESPONSE_TIMEOUT: float = 30.0
    AUDIO_CHUNK_SIZE: int = 512
    
    # Debug Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        if not cls.OPENROUTER_API_KEY or cls.OPENROUTER_API_KEY == "your_api_key_here":
            print("ERROR: OPENROUTER_API_KEY not set in environment or .env file")
            return False
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """Setup logging directory."""
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Return the system prompt for Jarvis personality."""
        return """You are JARVIS, an advanced AI assistant inspired by Iron Man's companion.

PERSONALITY TRAITS:
- Intelligent and highly capable
- Concise and direct in responses
- Confident but not arrogant
- Slightly futuristic tone
- Helpful and proactive
- Witty but never annoying
- Professional yet personable

RESPONSE GUIDELINES:
- Keep responses brief and actionable (1-3 sentences typically)
- Use technical language when appropriate
- Show initiative in solving problems
- Acknowledge commands with brief confirmations
- Add subtle humor when fitting
- Never be verbose or overly explanatory

CAPABILITIES:
- Control PC applications and system functions
- Search files and manage folders
- Browse the web and summarize content
- Automate keyboard and mouse actions
- Take screenshots and manage windows
- Control volume, brightness, and system state

When executing commands, respond with brief confirmation like:
- "Opening Chrome now, sir."
- "Volume adjusted to 50%."
- "Screenshot captured and saved."

For questions, provide concise, accurate answers.

Current date/time context will be provided. Use it appropriately."""


# Initialize logging directory
Config.setup_logging()
