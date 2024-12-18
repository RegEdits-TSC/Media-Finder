import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from utils.create_env import create_env_file
from utils.exceptions import MissingEnvironmentVariableError, NoValidTrackersError
from rich.console import Console

from utils.logger import LOG_PREFIX_CONFIG, LOG_PREFIX_VALIDATE

console = Console()

# Load environment variables from the .env file located in the config directory
load_dotenv(dotenv_path=Path("config/.env"))

# API Keys and URLs
API_KEYS = {
    "TMDB_API_KEY": os.getenv("TMDB_API_KEY"),
    "ATH_API_KEY": os.getenv('ATH_API_KEY'),
    "BLU_API_KEY": os.getenv('BLU_API_KEY'),
    "FNP_API_KEY": os.getenv('FNP_API_KEY'),
    "HDB_API_KEY": os.getenv('HDB_API_KEY'),
    "LDU_API_KEY": os.getenv('LDU_API_KEY'),
    "LST_API_KEY": os.getenv('LST_API_KEY'),
    "OTW_API_KEY": os.getenv('OTW_API_KEY'),
    "OE_API_KEY": os.getenv('OE_API_KEY'),
    "PSS_API_KEY": os.getenv('PSS_API_KEY'),
    "RFX_API_KEY": os.getenv('RFX_API_KEY'),
    "ULCX_API_KEY": os.getenv('ULCX_API_KEY')
}

URLS = {
    "TMDB_URL": os.getenv('TMDB_URL'),
    "ATH_URL": os.getenv('ATH_URL'),
    "BLU_URL": os.getenv('BLU_URL'),
    "FNP_URL": os.getenv('FNP_URL'),
    "HDB_URL": os.getenv('HDB_URL'),
    "LDU_URL": os.getenv('LDU_URL'),
    "LST_URL": os.getenv('LST_URL'),
    "OTW_URL": os.getenv('OTW_URL'),
    "OE_URL": os.getenv('OE_URL'),
    "PSS_URL": os.getenv('PSS_URL'),
    "RFX_URL": os.getenv('RFX_URL'),
    "ULCX_URL": os.getenv('ULCX_URL')
}

# List of tracker sites with their corresponding API key and URL environment variable names, names, and codes
TRACKER_SITES = [
    ("ATH_API_KEY", "ATH_URL", "Aither", "ATH"),
    ("BLU_API_KEY", "BLU_URL", "Blutopia", "BLU"),
    ("FNP_API_KEY", "FNP_URL", "FearNoPeer", "FNP"),
    ("HDB_API_KEY", "HDB_URL", "HDBits", "HDB"),
    ("LDU_API_KEY", "LDU_URL", "TheLDU", "LDU"),
    ("LST_API_KEY", "LST_URL", "L0ST", "LST"),
    ("OTW_API_KEY", "OTW_URL", "OldToons.World", "OTW"),
    ("OE_API_KEY", "OE_URL", "OnlyEncodes", "OE"),
    ("PSS_API_KEY", "PSS_URL", "PrivateSilverScreen", "PSS"),
    ("RFX_API_KEY", "RFX_URL", "ReelFliX", "RFX"),
    ("ULCX_API_KEY", "ULCX_URL", "Upload.cx", "ULCX")
]

def validate_env_vars(logger: logging.Logger) -> dict:
    """Validate that required environment variables are set."""
    try:
        # Check for missing required API keys and URLs
        required_keys = ["TMDB_API_KEY", "TMDB_URL"]
        missing_required = [key for key in required_keys if not os.getenv(key)]
        if missing_required:
            error_message = f"Missing required environment variables: {', '.join(missing_required)}"
            logger.error(f"{LOG_PREFIX_VALIDATE} {error_message}")
            raise MissingEnvironmentVariableError(missing_required)

        # Check for valid tracker API key and URL pairs
        valid_trackers = [
            {
                "api_key": os.getenv(api_key_var),
                "url": os.getenv(url_var),
                "name": tracker_name,
                "code": tracker_code
            }
            for api_key_var, url_var, tracker_name, tracker_code in TRACKER_SITES
            if os.getenv(api_key_var) and os.getenv(url_var)
        ]

        # If no valid trackers are found, log an error and raise an exception
        if not valid_trackers:
            error_message = (
                "At least one valid tracker API key and URL pair is required "
                f"from: {', '.join([f'{name} ({code})' for _, _, name, code in TRACKER_SITES])}"
            )
            logger.error(f"{LOG_PREFIX_VALIDATE} {error_message}")
            raise NoValidTrackersError(error_message)

        # Log disabled trackers due to missing or empty values
        disabled_trackers = [
            {"name": name, "code": code}
            for api_key, url, name, code in TRACKER_SITES
            if not os.getenv(api_key) or not os.getenv(url) or os.getenv(api_key) == "" or os.getenv(url) == ""
        ]
        if disabled_trackers:
            logger.warning(
                f"{LOG_PREFIX_VALIDATE} The following trackers are disabled due to missing or empty values: "
                + ", ".join([f"{tracker['name']} ({tracker['code']})" for tracker in disabled_trackers])
            )

        logger.info(f"{LOG_PREFIX_VALIDATE} Environment variables validated successfully.")

        # Return validated environment variables and trackers
        return {
            "required": {key: os.getenv(key) for key in required_keys},
            "trackers": valid_trackers,
        }

    except MissingEnvironmentVariableError as e:
        logger.error(f"{LOG_PREFIX_CONFIG} MissingEnvironmentVariableError: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except NoValidTrackersError as e:
        logger.error(f"{LOG_PREFIX_CONFIG} NoValidTrackersError: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except Exception as e:
        logger.error(f"{LOG_PREFIX_CONFIG} An unexpected error occurred: {str(e)}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        raise

def setup_environment(overwrite: bool, logger: logging.Logger) -> dict:
    """Setup the environment by creating or validating the .env file."""
    # Create or overwrite the .env file
    create_env_file(logger, overwrite=overwrite)
    # Validate the environment variables
    return validate_env_vars(logger)