import logging
from pathlib import Path
from rich.console import Console
import sys
from utils.exceptions import EnvFileCreationError

console = Console()

# Define the environment file content
ENV_CONTENT = """
# TMDb API Key
TMDB_API_KEY=

# TMDb Site URL
TMDB_URL=https://api.themoviedb.org/3/

# Site API Keys
ATH_API_KEY=
BLU_API_KEY=
FNP_API_KEY=
LST_API_KEY=
OTW_API_KEY=
PSS_API_KEY=
RFX_API_KEY=
ULCX_API_KEY=

# Site URLs
ATH_URL=https://aither.cc/api/torrents/filter
BLU_URL=https://blutopia.cc/api/torrents/filter
FNP_URL=https://fearnopeer.com/api/torrents/filter
LST_URL=https://lst.gg/api/torrents/filter
OTW_URL=https://oldtoons.world/api/torrents/filter
PSS_URL=https://privatesilverscreen.cc/api/torrents/filter
RFX_URL=https://reelflix.xyz/api/torrents/filter
ULCX_URL=https://upload.cx/api/torrents/filter
"""

def create_env_file(file_path: str = "config/.env", overwrite: bool = False) -> None:
    """Create an .env file with preset values if it does not already exist or overwrite is enabled."""
    file_path = Path(file_path)

    if file_path.exists() and not overwrite:
        message = f"{file_path} already exists. Skipping creation."
        logging.info(message)
        return

    if file_path.exists() and overwrite:
        message = f"{file_path} exists but will be overwritten."
        console.print(f"[bold yellow]{message}[/bold yellow]")
        logging.info(message)

    try:
        # Use a context manager to ensure the file is properly closed
        with file_path.open("w") as file:
            file.write(ENV_CONTENT)
        message = f"{file_path} has been created. Please edit the file with your configuration values and rerun the script."
        console.print(f"[bold green]{message}[/bold green]")
        logging.info(message)
        sys.exit(0)  # Exit the script after creating the file
    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {str(e)}")
        raise EnvFileCreationError(file_path, f"File not found: {str(e)}")
    except PermissionError as e:
        logging.error(f"PermissionError: {str(e)}")
        raise EnvFileCreationError(file_path, f"Permission denied: {str(e)}")
    except IOError as e:
        logging.error(f"IOError: {str(e)}")
        raise EnvFileCreationError(file_path, f"I/O error: {str(e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise EnvFileCreationError(file_path, f"An unexpected error occurred: {str(e)}")