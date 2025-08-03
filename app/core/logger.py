
import logging
import sys

try:
    from colorlog import ColoredFormatter
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

LOG_FORMAT = "% (asctime)s | %(log_color)s%(levelname)s%(reset)s | %(name)s | %(message)s" if COLORLOG_AVAILABLE else "% (asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_LEVEL = logging.DEBUG

def setup_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    if not logger.handlers:
        # Console handler with color support if available
        ch = logging.StreamHandler(sys.stdout)
        if COLORLOG_AVAILABLE:
            formatter = ColoredFormatter(LOG_FORMAT)
        else:
            formatter = logging.Formatter(LOG_FORMAT)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler for persistent logs
        fh = logging.FileHandler("app.log")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(fh)
    logger.propagate = False
    return logger
