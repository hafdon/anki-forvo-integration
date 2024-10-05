import logging
from logging.handlers import RotatingFileHandler
import coloredlogs

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

# Define the log format
log_format = "%(asctime)s - %(levelname)s - %(message)s"

# Install coloredlogs with the desired format
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt=log_format,
    level_styles={
        "debug": {"color": "blue"},
        "info": {"color": "green"},
        "warning": {"color": "yellow"},
        "error": {"color": "red"},
        "critical": {"color": "red", "bold": True},
    },
)

# Create a RotatingFileHandler
rotating_handler = RotatingFileHandler(
    "app.log", maxBytes=5 * 1024 * 1024, backupCount=3
)  # 5MB per file, keep 3 backups
rotating_handler.setLevel(logging.DEBUG)
rotating_formatter = logging.Formatter(log_format)
rotating_handler.setFormatter(rotating_formatter)

# Add the handler to the logger
logger.addHandler(rotating_handler)

# Example log messages
# for i in range(100000):
#     logger.debug(f"Debug message {i}")
