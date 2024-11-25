import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from utils.create_env import create_env_file
from utils.exceptions import MissingEnvironmentVariableError, NoValidTrackersError
from rich.console import Console

console = Console()

# Load environment variables from the .env file located in the config directory
load_dotenv(dotenv_path=Path("config/.env"))

# API Keys and URLs
API_KEYS = {
    "TMDB_API_KEY": os.getenv("TMDB_API_KEY"),
    "ATH_API_KEY": os.getenv('ATH_API_KEY'),
    "ULCX_API_KEY": os.getenv('ULCX_API_KEY'),
    "LST_API_KEY": os.getenv('LST_API_KEY'),
    "FNP_API_KEY": os.getenv('FNP_API_KEY'),
    "OTW_API_KEY": os.getenv('OTW_API_KEY'),
    "RFX_API_KEY": os.getenv('RFX_API_KEY'),
    "PSS_API_KEY": os.getenv('PSS_API_KEY')
}

URLS = {
    "TMDB_URL": os.getenv('TMDB_URL'),
    "ATH_URL": os.getenv('ATH_URL'),
    "ULCX_URL": os.getenv('ULCX_URL'),
    "LST_URL": os.getenv('LST_URL'),
    "FNP_URL": os.getenv('FNP_URL'),
    "OTW_URL": os.getenv('OTW_URL'),
    "RFX_URL": os.getenv('RFX_URL'),
    "PSS_URL": os.getenv('PSS_URL')
}

# List of tracker sites with their corresponding API key and URL environment variable names, names, and codes
TRACKER_SITES = [
    ("ATH_API_KEY", "ATH_URL", "Aither", "ATH"),
    ("ULCX_API_KEY", "ULCX_URL", "Upload.cx", "ULCX"),
    ("LST_API_KEY", "LST_URL", "L0ST", "LST"),
    ("FNP_API_KEY", "FNP_URL", "FearNoPeer", "FNP"),
    ("OTW_API_KEY", "OTW_URL", "OldToons.World", "OTW"),
    ("RFX_API_KEY", "RFX_URL", "ReelFliX", "RFX"),
    ("PSS_API_KEY", "PSS_URL", "PrivateSilverScreen", "PSS")
]

def validate_env_vars():
    """Validate that required environment variables are set."""
    try:
        # Check for missing required API keys and URLs
        required_keys = ["TMDB_API_KEY", "TMDB_URL"]
        missing_required = [key for key in required_keys if not os.getenv(key)]
        if missing_required:
            error_message = f"Missing required environment variables: {', '.join(missing_required)}"
            logging.error(error_message)
            raise MissingEnvironmentVariableError(error_message)

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
            logging.error(error_message)
            console.print(f"[bold red]Error:[/bold red] {error_message}")
            raise NoValidTrackersError(error_message)

        # Log disabled trackers due to missing or empty values
        disabled_trackers = [
            {"name": name, "code": code}
            for api_key, url, name, code in TRACKER_SITES
            if not os.getenv(api_key) or not os.getenv(url) or os.getenv(api_key) == "" or os.getenv(url) == ""
        ]
        if disabled_trackers:
            logging.warning(
                "The following trackers are disabled due to missing or empty values: "
                + ", ".join([f"{tracker['name']} ({tracker['code']})" for tracker in disabled_trackers])
            )

        logging.info("Environment variables validated successfully.")

        # Return validated environment variables and trackers
        return {
            "required": {key: os.getenv(key) for key in required_keys},
            "trackers": valid_trackers,
        }

    except MissingEnvironmentVariableError as e:
        logging.error(f"MissingEnvironmentVariableError: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except NoValidTrackersError as e:
        logging.error(f"NoValidTrackersError: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {str(e)}")
        raise

def setup_environment(overwrite: bool) -> dict:
    """Setup the environment by creating or validating the .env file."""
    # Create or overwrite the .env file
    create_env_file(overwrite=overwrite)
    # Validate the environment variables
    return validate_env_vars()