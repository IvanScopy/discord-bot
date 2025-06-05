"""
Bot Configuration
Quản lý tất cả cấu hình của Discord Bot
"""

import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration class"""
    
    # Discord Configuration
    DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
    DISCORD_APPLICATION_ID: Final[str] = os.getenv('DISCORD_APPLICATION_ID')
    
    # API Keys
    WEATHER_API_KEY: Final[str] = os.getenv('WEATHER_API_KEY')
    OPENAI_API_KEY: Final[str] = os.getenv('OPENAI_APIKEY')
    PEXELS_API_KEY: Final[str] = os.getenv('P_APIKEY')
    UNSPLASH_API_KEY: Final[str] = os.getenv('UnS_APIKEY')
    
    # Bot Settings
    COMMAND_PREFIX: Final[str] = os.getenv('COMMAND_PREFIX', '!')
    BOT_NAME: Final[str] = os.getenv('BOT_NAME', 'Discord Bot')
    BOT_VERSION: Final[str] = "2.0.0"
    
    # Database Configuration
    DATABASE_PATH: Final[str] = os.getenv('DATABASE_PATH', 'data/bot_database.db')
    
    # Logging Configuration
    LOG_LEVEL: Final[str] = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: Final[str] = os.getenv('LOG_DIR', 'logs')
    
    # Music Configuration
    MAX_QUEUE_SIZE: Final[int] = int(os.getenv('MAX_QUEUE_SIZE', '100'))
    DEFAULT_VOLUME: Final[float] = float(os.getenv('DEFAULT_VOLUME', '0.5'))
    
    # File Upload Limits
    MAX_FILE_SIZE: Final[int] = int(os.getenv('MAX_FILE_SIZE', '26214400'))  # 25MB
    
    # Reminder Configuration
    MAX_REMINDERS_PER_USER: Final[int] = int(os.getenv('MAX_REMINDERS_PER_USER', '50'))
    
    # Event Configuration
    MAX_EVENTS_PER_GUILD: Final[int] = int(os.getenv('MAX_EVENTS_PER_GUILD', '100'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            'DISCORD_TOKEN',
            'DISCORD_APPLICATION_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @classmethod
    def get_optional_features(cls) -> dict:
        """Get status of optional features"""
        return {
            'weather': bool(cls.WEATHER_API_KEY),
            'openai': bool(cls.OPENAI_API_KEY),
            'pexels': bool(cls.PEXELS_API_KEY),
            'unsplash': bool(cls.UNSPLASH_API_KEY)
        }

# Bot intents configuration
def get_bot_intents():
    """Configure bot intents"""
    import discord
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    intents.guild_messages = True
    intents.guild_reactions = True
    intents.members = True  # For user info features
    
    return intents

# Cog configuration
COGS = [
    'bot.cogs.music',
    'bot.cogs.weather',
    'bot.cogs.utilities',
    'bot.cogs.events',
    'bot.cogs.reminders',
    'bot.cogs.media_sharing',
    'bot.cogs.user_info',
    'bot.cogs.search',
    'bot.cogs.video'
]

# Embed colors
class Colors:
    """Standard colors for embeds"""
    PRIMARY = 0x0099ff
    SUCCESS = 0x00ff00
    WARNING = 0xffa500
    ERROR = 0xff0000
    INFO = 0x17a2b8
    MUSIC = 0x9b59b6
    EVENT = 0xe74c3c
    REMINDER = 0xf39c12

# Emojis
class Emojis:
    """Standard emojis for bot responses"""
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    MUSIC = "🎵"
    PLAY = "▶️"
    PAUSE = "⏸️"
    STOP = "⏹️"
    SKIP = "⏭️"
    VOLUME = "🔊"
    QUEUE = "📋"
    EVENT = "🎉"
    REMINDER = "⏰"
    MEDIA = "📎"
    USER = "👤"
    SEARCH = "🔍"
