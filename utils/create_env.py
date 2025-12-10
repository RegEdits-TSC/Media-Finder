# Standard library imports
import logging
import sys
from pathlib import Path
from textwrap import dedent

# Third-party library imports
from rich.console import Console

# Local imports
from utils.exceptions import EnvFileCreationError
from utils.logger import LOG_PREFIX_CONFIG

console = Console()

# Define the environment file content
ENV_CONTENT = dedent("""
    # TMDb API Key
    TMDB_API_KEY=

    # TMDb Site URL
    TMDB_URL=https://api.themoviedb.org/3/

    # Site API Keys
    ATH_API_KEY=
    BHD_API_KEY=
    BLU_API_KEY=
    FNP_API_KEY=
    LDU_API_KEY=
    LST_API_KEY=
    OTW_API_KEY=
    OE_API_KEY=
    RFX_API_KEY=
    ULCX_API_KEY=

    # Site URLs
    ATH_URL=https://aither.cc/api/torrents/filter
    BHD_URL=https://beyond-hd.me/api/torrents/filter
    BLU_URL=https://blutopia.cc/api/torrents/filter
    FNP_URL=https://fearnopeer.com/api/torrents/filter
    LDU_URL=https://theldu.to/api/torrents/filter
    LST_URL=https://lst.gg/api/torrents/filter
    OTW_URL=https://oldtoons.world/api/torrents/filter
    OE_URL=https://onlyencodes.cc/api/torrents/filter
    RFX_URL=https://reelflix.cc/api/torrents/filter
    ULCX_URL=https://upload.cx/api/torrents/filter
""")

def create_env_file(
    logger: logging.Logger, 
    file_path: str = "config/.env", 
    overwrite: bool = False
) -> None:
    """
    Create an .env file with preset values if it does not already exist or overwrite is enabled.
    """
    file_path = Path(file_path)

    # Handle existing file cases
    if file_path.exists():
        if overwrite:
            message = f"{file_path} exists but will be overwritten."
            console.print(f"[bold yellow]{message}[/bold yellow]")
            logger.info(f"{LOG_PREFIX_CONFIG} {message}")
        else:
            message = f"{file_path} already exists. Skipping creation."
            logger.info(f"{LOG_PREFIX_CONFIG} {message}")
            return

    try:
        # Write the .env file with preset content
        file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        with file_path.open("w", encoding="utf-8") as file:
            file.write(ENV_CONTENT)

        message = f"{file_path} has been created. Please edit the file with your configuration values and rerun the script."
        console.print(f"[bold green]{message}[/bold green]")
        logger.info(f"{LOG_PREFIX_CONFIG} {message}")
        sys.exit(0)  # Exit the script after creating the file

    except (FileNotFoundError, PermissionError, IOError) as e:
        error_type = type(e).__name__
        logger.error(f"{LOG_PREFIX_CONFIG} {error_type}: {str(e)}")
        raise EnvFileCreationError(file_path, f"{error_type}: {str(e)}")

    except Exception as e:
        logger.error(f"{LOG_PREFIX_CONFIG} An unexpected error occurred: {str(e)}")
        raise EnvFileCreationError(file_path, f"An unexpected error occurred: {str(e)}")