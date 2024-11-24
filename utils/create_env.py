import os
import logging
import sys
from rich.console import Console

console = Console()

def create_env_file(file_path="config/.env", overwrite=False):
    """Create an .env file with preset values if it does not already exist or overwrite is enabled."""
    env_content = """
# TMDb API Key
TMDB_API_KEY=

# TMDb Site URL
TMDB_URL=https://api.themoviedb.org/3/

# Site API Keys
ATH_API_KEY=
ULCX_API_KEY=
LST_API_KEY=
FNP_API_KEY=
OTW_API_KEY=
RFX_API_KEY=
PSS_API_KEY=

# Site URLs
ATH_URL=https://aither.cc/api/torrents/filter
ULCX_URL=https://upload.cx/api/torrents/filter
LST_URL=https://lst.gg/api/torrents/filter
FNP_URL=https://fearnopeer.com/api/torrents/filter
OTW_URL=https://oldtoons.world/api/torrents/filter
RFX_URL=https://reelflix.xyz/api/torrents/filter
PSS_URL=https://privatesilverscreen.cc/api/torrents/filter
""".strip()

    if os.path.exists(file_path):
        if overwrite:
            message = f"{file_path} exists but will be overwritten."
            console.print(f"[bold yellow]{message}[/bold yellow]")
            logging.info(message)
        else:
            message = f"{file_path} already exists. Skipping creation."
            logging.info(message)
            return

    try:
        with open(file_path, "w") as file:
            file.write(env_content)
        message = f"{file_path} has been created successfully. Please update this file with the correct API keys before running the script again."
        console.print(f"[bold green]{message}[/bold green]")
        logging.info(message)
        sys.exit(0)  # Exit the script successfully
    except Exception as e:
        message = f"An error occurred while creating {file_path}: {e}"
        console.print(f"[bold red]{message}[/bold red]")
        logging.error(message)
        sys.exit(1)  # Exit with an error status