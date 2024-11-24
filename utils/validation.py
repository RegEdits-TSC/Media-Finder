import logging
import os
from dotenv import load_dotenv
from rich.console import Console

console = Console()

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# API Keys
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
ATH_API_KEY = os.getenv('ATH_API_KEY')
ULCX_API_KEY = os.getenv('ULCX_API_KEY')
LST_API_KEY = os.getenv('LST_API_KEY')
FNP_API_KEY = os.getenv('FNP_API_KEY')
OTW_API_KEY = os.getenv('OTW_API_KEY')
RFX_API_KEY = os.getenv('RFX_API_KEY')
PSS_API_KEY = os.getenv('PSS_API_KEY')

# Site URLs
TMDB_URL = os.getenv('TMDB_URL')
ATH_URL = os.getenv('ATH_URL')
ULCX_URL = os.getenv('ULCX_URL')
LST_URL = os.getenv('LST_URL')
FNP_URL = os.getenv('FNP_URL')
OTW_URL = os.getenv('OTW_URL')
RFX_URL = os.getenv('RFX_URL')
PSS_URL = os.getenv('PSS_URL')

def validate_env_vars():
    """Validate that required environment variables are set."""
    # Mandatory variables
    required_vars = {
        "TMDB_API_KEY": TMDB_API_KEY,
        "TMDB_URL": TMDB_URL,
    }

    # List of tracker API and URL with additional information
    tracker_sites = [
        ("ATH_API_KEY", "ATH_URL", "Aither", "ATH"),
        ("ULCX_API_KEY", "ULCX_URL", "Upload.cx", "ULCX"),
        ("LST_API_KEY", "LST_URL", "L0ST", "LST"),
        ("FNP_API_KEY", "FNP_URL", "FearNoPeer", "FNP"),
        ("OTW_API_KEY", "OTW_URL", "OldToons.World", "OTW"),
        ("RFX_API_KEY", "RFX_URL", "ReelFliX", "RFX"),
        ("PSS_API_KEY", "PSS_URL", "PrivateSilverScreen", "PSS"),
    ]

    # Check required variables
    missing_required = [key for key, value in required_vars.items() if not value]
    if missing_required:
        error_message = f"Missing required environment variables: {', '.join(missing_required)}"
        logging.error(error_message)
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        exit()

    # Check tracker pairs
    valid_trackers = []
    for api_key_var, url_var, tracker_name, tracker_code in tracker_sites:
        api_key = os.getenv(api_key_var)
        url = os.getenv(url_var)

        if api_key and url:
            valid_trackers.append({
                "api_key": api_key,
                "url": url,
                "name": tracker_name,
                "code": tracker_code,
            })
        else:
            logging.warning(f"{tracker_name} ({tracker_code}) is missing API key or URL.")

    if not valid_trackers:
        error_message = (
            "At least one valid tracker API key and URL pair is required "
            f"from: {', '.join([f'{name} ({code})' for _, _, name, code in tracker_sites])}"
        )
        logging.error(error_message)
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        exit()

    # Log disabled trackers
    disabled_trackers = [
        {"name": name, "code": code}
        for api_key, url, name, code in tracker_sites
        if not (os.getenv(api_key) and os.getenv(url))
    ]
    if disabled_trackers:
        logging.warning(
            "The following trackers are disabled due to missing values: "
            + ", ".join([f"{tracker['name']} ({tracker['code']})" for tracker in disabled_trackers])
        )


    logging.info("Environment variables validated successfully.")

    # Return validated environment variables and trackers
    return {
        "required": required_vars,
        "trackers": valid_trackers,
    }