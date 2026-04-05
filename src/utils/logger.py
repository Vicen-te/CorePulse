"""
Application logger.

Provides a configured logger that writes to
~/.local/state/corepulse/corepulse.log with automatic rotation.
"""

# Standard library
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path.home() / ".local" / "state" / "corepulse"
_LOG_FILE = _LOG_DIR / "corepulse.log"
_MAX_BYTES = 1_000_000  # 1 MB
_BACKUP_COUNT = 2
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with file + stderr handlers (configured once)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler with rotation
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT,
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(fh)

    # Stderr handler (warnings and above)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(sh)

    return logger
