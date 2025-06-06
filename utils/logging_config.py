import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from utils.database import db_manager

class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes logs to the database"""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
    
    def emit(self, record):
        """Emit a log record to the database"""
        try:
            # Extract additional information from the record
            user_id = getattr(record, 'user_id', None)
            guild_id = getattr(record, 'guild_id', None)
            module = getattr(record, 'module', record.name)
            
            # Format the message
            message = self.format(record)
            
            # Use asyncio to run the async database operation
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule the coroutine
                    asyncio.create_task(self.db_manager.log_event(
                        level=record.levelname,
                        message=message,
                        module=module,
                        user_id=user_id,
                        guild_id=guild_id
                    ))
                else:
                    # If we're not in an async context, run it
                    loop.run_until_complete(self.db_manager.log_event(
                        level=record.levelname,
                        message=message,
                        module=module,
                        user_id=user_id,
                        guild_id=guild_id
                    ))
            except RuntimeError:
                # If no event loop is running, create a new one
                asyncio.run(self.db_manager.log_event(
                    level=record.levelname,
                    message=message,
                    module=module,
                    user_id=user_id,
                    guild_id=guild_id
                ))
        except Exception as e:
            # Don't let logging errors crash the application
            print(f"Error logging to database: {e}")

class BotLogger:
    """Enhanced logging system for the Discord bot"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.setup_logging()
    
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for general logs (with rotation)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, 'bot.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(self.log_dir, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Database handler
        try:
            db_handler = DatabaseLogHandler(db_manager)
            db_handler.setLevel(logging.WARNING)  # Only log warnings and above to DB
            db_handler.setFormatter(simple_formatter)
            root_logger.addHandler(db_handler)
        except Exception as e:
            print(f"Could not setup database logging: {e}")
        
        # Discord.py specific logging
        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.WARNING)
        
        # Bot specific loggers
        self.setup_module_loggers()
    
    def setup_module_loggers(self):
        """Setup loggers for specific bot modules"""
        modules = ['commands', 'events', 'music', 'reminders', 'database', 'media']
        
        for module in modules:
            logger = logging.getLogger(f'bot.{module}')
            logger.setLevel(logging.DEBUG)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger for a specific module"""
        return logging.getLogger(f'bot.{name}')
    
    @staticmethod
    def log_command_usage(command_name: str, user_id: int, guild_id: int, 
                         success: bool = True, error: str = None):
        """Log command usage with context"""
        logger = BotLogger.get_logger('commands')
        
        if success:
            logger.info(
                f"Command '{command_name}' executed successfully",
                extra={'user_id': user_id, 'guild_id': guild_id, 'module': 'commands'}
            )
        else:
            logger.error(
                f"Command '{command_name}' failed: {error}",
                extra={'user_id': user_id, 'guild_id': guild_id, 'module': 'commands'}
            )
    
    @staticmethod
    def log_user_action(action: str, user_id: int, guild_id: int, details: str = None):
        """Log user actions"""
        logger = BotLogger.get_logger('events')
        message = f"User action: {action}"
        if details:
            message += f" - {details}"

        logger.info(
            message,
            extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'events'}
        )
    
    @staticmethod
    def log_error(error: Exception, context: str = None, user_id: int = None,
                 guild_id: int = None):
        """Log errors with context"""
        logger = BotLogger.get_logger('errors')
        message = f"Error in {context}: {str(error)}" if context else str(error)

        logger.error(
            message,
            exc_info=True,
            extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'errors'}
        )
    
    @staticmethod
    def log_music_action(action: str, guild_id: int, user_id: int, details: str = None):
        """Log music-related actions"""
        logger = BotLogger.get_logger('music')
        message = f"Music action: {action}"
        if details:
            message += f" - {details}"

        logger.info(
            message,
            extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'music'}
        )
    
    @staticmethod
    def log_database_operation(operation: str, table: str, success: bool = True, 
                              error: str = None):
        """Log database operations"""
        logger = BotLogger.get_logger('database')
        
        if success:
            logger.debug(f"Database operation successful: {operation} on {table}")
        else:
            logger.error(f"Database operation failed: {operation} on {table} - {error}")
    
    @staticmethod
    def log_reminder_action(action: str, reminder_id: int, user_id: int,
                           guild_id: int, details: str = None):
        """Log reminder-related actions"""
        logger = BotLogger.get_logger('reminders')
        message = f"Reminder {action}: ID {reminder_id}"
        if details:
            message += f" - {details}"

        logger.info(
            message,
            extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'reminders'}
        )
    
    @staticmethod
    def log_media_share(media_type: str, user_id: int, guild_id: int,
                       success: bool = True, error: str = None):
        """Log media sharing actions"""
        logger = BotLogger.get_logger('media')

        if success:
            logger.info(
                f"Media shared successfully: {media_type}",
                extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'media'}
            )
        else:
            logger.error(
                f"Media sharing failed: {media_type} - {error}",
                extra={'user_id': user_id, 'guild_id': guild_id, 'bot_module': 'media'}
            )

# Global bot logger instance (initialized by setup_logging)
bot_logger = None

# Convenience functions for easy access
def setup_logging():
    """Setup logging system - convenience function"""
    global bot_logger
    bot_logger = BotLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module"""
    return BotLogger.get_logger(name)

def log_command(command_name: str, user_id: int, guild_id: int, 
               success: bool = True, error: str = None):
    """Log command usage"""
    BotLogger.log_command_usage(command_name, user_id, guild_id, success, error)

def log_error(error: Exception, context: str = None, user_id: int = None, 
             guild_id: int = None):
    """Log errors"""
    BotLogger.log_error(error, context, user_id, guild_id)

def log_user_action(action: str, user_id: int, guild_id: int, details: str = None):
    """Log user actions"""
    BotLogger.log_user_action(action, user_id, guild_id, details)
