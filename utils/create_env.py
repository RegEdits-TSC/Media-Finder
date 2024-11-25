import logging
from pathlib import Path
from rich.console import Console

console = Console()

def create_env_file(file_path: str = "config/.env", overwrite: bool = False) -> None:
    """Create an .env file with preset values if it does not already exist or overwrite is enabled."""
    env_content = """
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

    file_path = Path(file_path)

    if file_path.exists():
        if overwrite:
            message = f"{file_path} exists but will be overwritten."
            console.print(f"[bold yellow]{message}[/bold yellow]")
            logging.info(message)
        else:
            message = f"{file_path} already exists. Skipping creation."
            logging.info(message)
            return

    try:
        with file_path.open("w") as file:
            file.write(env_content)
        message = f"{file_path} has been created."
        console.print(f"[bold green]{message}[/bold green]")
        logging.info(message)
    except Exception as e:
        message = f"Failed to create {file_path}: {e}"
        console.print(f"[bold red]{message}[/bold red]")
        logging.error(message)