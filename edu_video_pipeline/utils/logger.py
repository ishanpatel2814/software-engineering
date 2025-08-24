"""
utils/logger.py

Logging functionality for the PDF/PPT to Educational Video Pipeline.

Features:
- Colored console logs when `colorlog` is available; clean fallback otherwise.
- Safe handling of log file paths (no makedirs('') errors).
- Idempotent setup (won't duplicate handlers on re-init).
- Progress bar helper for pipeline steps.
"""

from __future__ import annotations

import os
import sys
import logging
from typing import Optional, Union

# Try to use colorlog for pretty console output; fall back to plain logging if unavailable
try:
    from colorlog import ColoredFormatter  # correct class name
    _HAS_COLORLOG = True
except Exception:
    _HAS_COLORLOG = False


def _coerce_level(level: Optional[Union[str, int]]) -> int:
    """
    Coerce a string/int level into a logging level int. Defaults to INFO.
    """
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        candidate = getattr(logging, level.upper(), None)
        if isinstance(candidate, int):
            return candidate
    return logging.INFO


def setup_logger(log_level: Optional[Union[str, int]] = "INFO",
                 log_file: Optional[str] = None) -> logging.Logger:
    """
    Create or reconfigure the pipeline logger.

    Args:
        log_level: Logging level (e.g., "DEBUG", "INFO") or int.
        log_file: Optional path to a log file. If a bare filename is provided,
                  it will be written to the current working directory.

    Returns:
        A configured `logging.Logger` named "edu_video_pipeline".
    """
    logger = logging.getLogger("edu_video_pipeline")
    logger.setLevel(_coerce_level(log_level))
    logger.propagate = False  # prevent duplicate logs via root handlers

    # Remove any existing handlers to avoid duplicates when called multiple times
    for h in list(logger.handlers):
        logger.removeHandler(h)

    # ----- Console handler -----
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logger.level)

    if _HAS_COLORLOG:
        # Colored console output
        fmt = "%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s %(message)s"
        color_formatter = ColoredFormatter(
            fmt,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
        ch.setFormatter(color_formatter)
    else:
        # Plain console output
        plain_fmt = "%(levelname)-8s [%(name)s] %(message)s"
        ch.setFormatter(logging.Formatter(plain_fmt))

    logger.addHandler(ch)

    # ----- Optional file handler -----
    if log_file:
        # Normalize path and safely create parent directory if present
        lf = os.path.abspath(str(log_file).strip())
        dirpath = os.path.dirname(lf)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        fh = logging.FileHandler(lf, encoding="utf-8")
        fh.setLevel(logger.level)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)

    return logger


def log_pipeline_progress(logger: logging.Logger, message: str, step: int, total_steps: int) -> None:
    """
    Log progress in the pipeline with a progress indicator.

    Args:
        logger: Logger instance.
        message: Progress message.
        step: Current step number (1-based).
        total_steps: Total number of steps (>= 1).
    """
    # Guard against bad inputs
    total_steps = max(1, int(total_steps))
    step = max(0, min(int(step), total_steps))

    progress_percentage = int((step / total_steps) * 100)
    bar_len = 20
    filled = int(round(progress_percentage / (100 / bar_len)))
    progress_bar = f"[{'=' * filled:<{bar_len}}] {progress_percentage:>3d}%"

    # Log via logger (shows in console and file if configured)
    logger.info(f"{progress_bar} {message}")

    # Also print an updating progress line to stdout for immediate feedback
    end_char = "" if step < total_steps else "\n"
    print(f"\r{progress_bar} {message}", end=end_char)
    sys.stdout.flush()
