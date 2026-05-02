"""Configure application logging to console and a rotating log file."""

from __future__ import annotations

import logging
import os
from pathlib import Path


def setup_logging(
    log_dir: str | Path | None = None,
    log_filename: str = "trading_bot.log",
    level: int = logging.INFO,
) -> Path:
    """
    Configure root logger with stream handler and file handler.

    Returns the path to the log file used.
    """
    log_dir = Path(log_dir or os.environ.get("TRADING_BOT_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_filename

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called twice
    for h in list(root.handlers):
        if getattr(h, "_trading_bot_handler", False):
            root.removeHandler(h)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh._trading_bot_handler = True  # type: ignore[attr-defined]
    root.addHandler(sh)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    fh._trading_bot_handler = True  # type: ignore[attr-defined]
    root.addHandler(fh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return log_path
