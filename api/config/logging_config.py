import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes= 5 * 1024 * 1024,   # max boyut 5mb
        backupCount=3,      # en fazla 3 log dosyası sakla
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)  # bivim belirler

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)