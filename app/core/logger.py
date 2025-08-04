# app/core/logger.py

import logging
import sys
from pathlib import Path
# Import the central settings object
from .config import settings

# Check for colorlog availability
try:
    from colorlog import ColoredFormatter
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

# This is the root directory of the project (e.g., project_root/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

def setup_logger(name: str) -> logging.Logger:
    """Sets up a customized logger using configuration from settings."""
    
    logger = logging.getLogger(name)
    # Get log level from settings, ensuring it's uppercase
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Prevent adding duplicate handlers
    if not logger.handlers:
        # Define a base format for reuse
        base_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
        
        # --- Console Handler ---
        ch = logging.StreamHandler(sys.stdout)
        if COLORLOG_AVAILABLE:
            color_format = "%(log_color)s" + base_format
            formatter = ColoredFormatter(color_format)
        else:
            formatter = logging.Formatter(base_format)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # --- File Handler ---
        # Create a robust path for the log file in the project root
        log_file_path = PROJECT_ROOT / settings.LOG_FILE
        log_file_path.parent.mkdir(exist_ok=True) # Ensure directory exists
        
        fh = logging.FileHandler(log_file_path)
        fh.setFormatter(logging.Formatter(base_format))
        logger.addHandler(fh)

    logger.propagate = False
    return logger

# Example of using the logger within this module itself
log = setup_logger(__name__)
log.info("Logger setup is complete.")