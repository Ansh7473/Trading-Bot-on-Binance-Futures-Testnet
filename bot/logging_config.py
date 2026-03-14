# --------------------------------------------------------------
# bot/logging_config.py – clean, focused logger configuration
# --------------------------------------------------------------
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Get the correct path
PROJECT_ROOT = Path.cwd()
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Full path of the rotating log file
LOG_FILE = LOG_DIR / "trading.log"

# Track configured loggers to avoid duplicates
_configured_loggers = {}

class TradingFormatter(logging.Formatter):
    """Custom formatter for trading logs"""
    
    def format(self, record):
        # Clean up module names
        if record.name.startswith('bot.'):
            module_name = record.name[4:]  # Remove 'bot.' prefix
        else:
            module_name = record.name
        
        # Format different log levels with colors and emojis
        level_icons = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '💥'
        }
        
        # Clean, readable format for console
        if record.levelname in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            timestamp = datetime.now().strftime("%H:%M:%S")
            icon = level_icons.get(record.levelname, '📝')
            return f"{timestamp} {icon} {record.getMessage()}"
        
        # Detailed format for debug and file
        return f"{self.formatTime(record)} | {record.levelname:8} | {module_name:15} | {record.getMessage()}"

def get_logger(name: str = "trading") -> logging.Logger:
    """
    Returns a clean logger focused on trading operations
    """
    # Use simplified logger names
    if name.startswith('bot.'):
        logger_name = name[4:]  # Remove 'bot.' prefix
    else:
        logger_name = name
    
    logger = logging.getLogger(logger_name)

    # Configure only once
    if logger_name not in _configured_loggers:
        logger.setLevel(logging.INFO)  # Default to INFO level
        
        # Clear any existing handlers
        logger.handlers.clear()

        # ------------------------------------------------------------------
        # File handler – detailed debug information
        # ------------------------------------------------------------------
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=5 * 1024 * 1024,   # 5 MB per file
                backupCount=3,               # keep last 3 files
                encoding="utf-8",
            )
            file_fmt = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
            )
            file_handler.setFormatter(file_fmt)
            file_handler.setLevel(logging.DEBUG)  # File gets everything
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️ Could not create file handler: {e}")

        # ------------------------------------------------------------------
        # Console handler – clean, user-friendly output
        # ------------------------------------------------------------------
        console_handler = logging.StreamHandler(sys.stdout)
        console_fmt = TradingFormatter()
        console_handler.setFormatter(console_fmt)
        console_handler.setLevel(logging.INFO)  # Console only shows important messages
        logger.addHandler(console_handler)

        _configured_loggers[logger_name] = True

    return logger

# Specialized loggers for different components
def get_order_logger():
    """Logger specifically for order-related messages"""
    return get_logger("orders")

def get_price_logger():
    """Logger for price and market data"""
    return get_logger("prices")

def get_error_logger():
    """Logger for errors and critical issues"""
    return get_logger("errors")

# Utility functions
def check_log_status():
    """Check if log file is being written properly"""
    if LOG_FILE.exists():
        size = LOG_FILE.stat().st_size
        return f"✅ Log file: {LOG_FILE} ({size} bytes)"
    else:
        return f"❌ Log file does not exist"

def view_recent_trades(lines=10):
    """View recent trading activity"""
    if not LOG_FILE.exists():
        print("No log file found")
        return
    
    print(f"📋 Recent trading activity (last {lines} lines):")
    print("=" * 60)
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines_content = f.readlines()[-lines:]
            for line in lines_content:
                if any(keyword in line for keyword in ['ORDER', 'BUY', 'SELL', 'FILLED', 'CANCEL']):
                    print(line.strip())
    except Exception as e:
        print(f"Error reading log file: {e}")

# Test the logging configuration
if __name__ == "__main__":
    logger = get_logger("test")
    logger.info("Testing clean logging configuration")
    logger.error("Test error message")
    
    order_logger = get_order_logger()
    order_logger.info("BUY 0.002 BTCUSDT @ market price")
    order_logger.info("Order FILLED: 0.002 BTCUSDT @ $72,500")
    
    print(check_log_status())
