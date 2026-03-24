import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json
from colorama import Fore, Style, init

# Initialize colorama for Windows
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(name: str = "ai_ops", level: int = logging.INFO) -> logging.Logger:
    """Setup logger with both file and console handlers."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console Handler (Colored)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    colored_formatter = ColoredFormatter(
        '%(asctime)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (JSON for structured logging)
    file_handler = logging.FileHandler(f'logs/ai_ops_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler.setLevel(logging.DEBUG)
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if hasattr(record, "extra_data"):
                log_obj["data"] = record.extra_data
            return json.dumps(log_obj)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

# Ensure logs directory exists
import os
os.makedirs("logs", exist_ok=True)

# Default logger instance
logger = setup_logger()

def log_agent_step(agent_name: str, step: str, data: Dict[str, Any] = None):
    """Helper function to log agent steps consistently."""
    extra = {"extra_data": data} if data else {}
    logger.info(f"[{agent_name.upper()}] {step}", extra=extra)