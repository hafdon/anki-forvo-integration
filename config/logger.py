import logging
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

# Create a FileHandler to write logs to a file
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)  # Set the level for file handler

# Define a formatter for the file handler
file_formatter = logging.Formatter(log_format)
file_handler.setFormatter(file_formatter)

# Add the FileHandler to the logger
logger.addHandler(file_handler)

# # Example log messages
# logger.debug("This is a DEBUG message.")
# logger.info("This is an INFO message.")
# logger.warning("This is a WARNING message.")
# logger.error("This is an ERROR message.")
# logger.critical("This is a CRITICAL message.")
