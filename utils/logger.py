import logging
from datetime import datetime
import os

# Logger Setup
def setup_logging(output_dir, debug_mode=False):
    """Setup logging configuration."""
    os.makedirs(output_dir, exist_ok=True)
    log_prefix = "[DEBUG] " if debug_mode else ""
    log_filename = datetime.now().strftime(f"{log_prefix}media_log-%H_%M_%S_%m_%d_%Y.log")
    log_filepath = os.path.join(output_dir, log_filename)
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        filename=log_filepath,
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging initialized.")
    if debug_mode:
        logging.debug("Debug mode enabled. All responses and execution steps will be logged.")