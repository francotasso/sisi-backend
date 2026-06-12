import logging
import sys

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(logger_name).setLevel(settings.LOG_LEVEL)
