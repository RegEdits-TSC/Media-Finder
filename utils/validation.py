# Standard library imports
import logging
import os
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from rich.console import Console

# Local imports
from utils.create_env import create_env_file
from utils.exceptions import MissingEnvironmentVariableError, NoValidTrackersError
from utils.logger import LOG_PREFIX_CONFIG, LOG_PREFIX_PROCESS, LOG_PREFIX_VALIDATE

console = Console()

# Load environment variables from the .env file located in the config directory
load_dotenv(dotenv_path=Path("config/.env"))

# Tracker site configurations
TRACKER_CONFIG = [
    {"key": "ATH", "name": "Aither"},
    {"key": "BHD", "name": "BeyondHD"},
    {"key": "BLU", "name": "Blutopia"},
    {"key": "FNP", "name": "FearNoPeer"},
    {"key": "LDU", "name": "TheLDU"},
    {"key": "LST", "name": "L0ST"},
    {"key": "OTW", "name": "OldToons.World"},
    {"key": "OE", "name": "OnlyEncodes"},
    {"key": "RFX", "name": "ReelFliX"},
    {"key": "ULCX", "name": "Upload.cx"},
]

# Define media type categories and their synonyms
MEDIA_TYPES = {
    "REMUX": {"remux"},
    "WEB-DL": {"web-dl"},
    "Encode": {"encode", "x264 encode", "x265 encode"},
    "Full Disc": {"full disc", "full disk"},
    "WEBRip": {"webrip", "web-rip"},
    "HDTV": {"hdtv"},
}

# Dynamically build API Keys and URLs from tracker configurations
API_KEYS = {f"{site['key']}_API_KEY": os.getenv(f"{site['key']}_API_KEY") for site in TRACKER_CONFIG}
URLS = {f"{site['key']}_URL": os.getenv(f"{site['key']}_URL") for site in TRACKER_CONFIG}

# Add TMDB to the keys and URLs separately
API_KEYS["TMDB_API_KEY"] = os.getenv("TMDB_API_KEY")
URLS["TMDB_URL"] = os.getenv("TMDB_URL")

# Build the tracker site list with API key and URL environment variable names
TRACKER_SITES = [
    (
        f"{site['key']}_API_KEY",
        f"{site['key']}_URL",
        site["name"],
        site["key"]
    )
    for site in TRACKER_CONFIG
]

def validate_env_vars(logger: logging.Logger) -> dict:
    """
    Validate that required environment variables are set.
    Returns:
        A dictionary containing validated required environment variables and trackers.
    """
    try:
        # Required environment variables
        required_keys = ["TMDB_API_KEY", "TMDB_URL"]

        # Check for missing required environment variables
        missing_required = [key for key in required_keys if not os.getenv(key)]
        if missing_required:
            error_message = f"Missing required environment variables: {', '.join(missing_required)}"
            logger.error(f"{LOG_PREFIX_VALIDATE} {error_message}")
            raise MissingEnvironmentVariableError(missing_required)

        # Validate tracker API key and URL pairs
        valid_trackers = []
        disabled_trackers = []

        for tracker in TRACKER_CONFIG:
            api_key_var = f"{tracker['key']}_API_KEY"
            url_var = f"{tracker['key']}_URL"
            api_key = API_KEYS.get(api_key_var)
            url = URLS.get(url_var)

            if api_key and url:
                valid_trackers.append({
                    "api_key": api_key,
                    "url": url,
                    "name": tracker["name"],
                    "code": tracker["key"],
                })
            else:
                disabled_trackers.append({"name": tracker["name"], "code": tracker["key"]})

        # Log and handle no valid trackers
        if not valid_trackers:
            error_message = (
                "At least one valid tracker API key and URL pair is required from: "
                + ", ".join([f"{tracker['name']} ({tracker['key']})" for tracker in TRACKER_CONFIG])
            )
            logger.error(f"{LOG_PREFIX_VALIDATE} {error_message}")
            raise NoValidTrackersError(error_message)

        # Log disabled trackers
        if disabled_trackers:
            logger.warning(
                f"{LOG_PREFIX_CONFIG} The following trackers are disabled due to missing or empty values: "
                + ", ".join([f"{tracker['name']} ({tracker['code']})" for tracker in disabled_trackers])
            )

        # Log successful validation
        logger.info(f"{LOG_PREFIX_VALIDATE} Environment variables validated successfully.")

        # Return validated environment variables and trackers
        return {
            "required": {key: os.getenv(key) for key in required_keys},
            "trackers": valid_trackers,
        }

    except MissingEnvironmentVariableError as e:
        logger.error(f"{LOG_PREFIX_CONFIG} Missing environment variables: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise

    except NoValidTrackersError as e:
        logger.error(f"{LOG_PREFIX_CONFIG} No valid trackers: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise

    except Exception as e:
        logger.error(f"{LOG_PREFIX_CONFIG} Unexpected error: {e}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        raise


def setup_environment(overwrite: bool, logger: logging.Logger) -> dict:
    """
    Set up the environment by creating or validating the .env file.
    Returns:
        A dictionary containing the validated environment variables.
    """
    try:
        # Create or overwrite the .env file
        logger.info(f"{LOG_PREFIX_VALIDATE} Starting environment setup. Overwrite: {overwrite}")
        create_env_file(logger, overwrite=overwrite)
        logger.info(f"{LOG_PREFIX_PROCESS} .env file setup completed.")

        # Validate the environment variables
        env_vars = validate_env_vars(logger)
        logger.info(f"{LOG_PREFIX_VALIDATE} Environment variables successfully validated.")
        return env_vars

    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} Failed to set up environment: {e}")
        raise  # Re-raise the exception to propagate it