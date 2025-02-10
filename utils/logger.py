import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

# Log Prefix Constants
LOG_PREFIX_VALIDATE = "[VALIDATE]"
LOG_PREFIX_JSON = "[JSON]"
LOG_PREFIX_SEARCH = "[SEARCH]"
LOG_PREFIX_API = "[API]"
LOG_PREFIX_FETCH = "[FETCH]"
LOG_PREFIX_SAVE = "[SAVE]"
LOG_PREFIX_INPUT = "[INPUT]"
LOG_PREFIX_PROCESS = "[PROCESS]"
LOG_PREFIX_OUTPUT = "[OUTPUT]"
LOG_PREFIX_CONFIG = "[CONFIG]"
LOG_PREFIX_TASK = "[TASK]"
LOG_PREFIX_RESULT = "[RESULT]"
LOG_PREFIX_SUMMARY = "[SUMMARY]"

class RedactingSensitiveInformation(logging.Formatter):
    """Formatter that redacts sensitive information in log messages."""
    def __init__(self, fmt=None, datefmt=None, sensitive_values=None):
        super().__init__(fmt, datefmt)
        self.sensitive_values = sensitive_values or []

    def format(self, record):
        message = super().format(record)
        for value in self.sensitive_values:
            if value:
                # Match sensitive values in different formats
                patterns = [
                    rf"\b{re.escape(value)}\b",  # Exact match
                    rf"(['\"]{re.escape(value)}['\"])",  # JSON-like match
                    rf"(api_key=){re.escape(value)}"  # Key-value pair match
                ]
                for pattern in patterns:
                    message = re.sub(pattern, r"[REDACTED]", message)
        return message

class CountingHandler(logging.Handler):
    """Custom handler to count log levels."""
    def __init__(self):
        super().__init__()
        self.error_count = 0
        self.warning_count = 0

    def emit(self, record):
        if record.levelno == logging.ERROR:
            self.error_count += 1
        elif record.levelno == logging.WARNING:
            self.warning_count += 1

def setup_logging(
    output_dir: Path,
    enable_logging: bool = False,
    debug_mode: bool = False,
    sensitive_values: Optional[List[str]] = None
) -> Tuple[logging.Logger, 'CountingHandler']:
    """Setup logging configuration with sensitive information redaction."""
    if not enable_logging:
        return None

    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Setup log filename
    now = datetime.now()
    log_prefix = "DEBUG_" if debug_mode else ""
    log_filename = now.strftime(f"{log_prefix}media_log-%H_%M_%S_%m_%d_%Y.log")
    log_filepath = Path(output_dir) / log_filename

    # Create the root logger
    logger = logging.getLogger()

    # --- Remove existing FileHandler instances ---
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Optionally, remove existing CountingHandler instances as well
    for handler in logger.handlers[:]:
        if handler.__class__.__name__ == "CountingHandler":  # or isinstance(handler, CountingHandler) if imported
            logger.removeHandler(handler)

    # Set the logger level based on debug_mode
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create and add a new FileHandler with the appropriate level and formatter
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    formatter = RedactingSensitiveInformation(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        sensitive_values=sensitive_values
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create and add a new CountingHandler
    counting_handler = CountingHandler()
    logger.addHandler(counting_handler)

    if sensitive_values:
        urllib3_logger = logging.getLogger("urllib3")
        urllib3_logger.handlers.clear()
        urllib3_logger.addHandler(file_handler)
        urllib3_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        urllib3_logger.propagate = False

    # Log initialization messages
    logger.info(f"{LOG_PREFIX_TASK} Logging initialized.")
    if debug_mode:
        logger.debug(f"{LOG_PREFIX_TASK} Debug mode enabled. All responses and execution steps will be logged.")
    logger.info(f"{LOG_PREFIX_TASK} Log file created: {log_filepath.resolve()}")

    return logger, counting_handler