import argparse
import logging
import os
from utils.validation import validate_env_vars
from utils.helpers import display_movie_details
from utils.logger import setup_logging
from utils.create_env import create_env_file
from cmds.processing import select_tmdb_result
from cmds.api_commands import search_tmdb, query_additional_apis
from rich.console import Console

console = Console()

# Determine the directory of the script and the output folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "logs")

# Argument parser
parser = argparse.ArgumentParser(description="Fetch movie/series details from TMDb using a TMDb ID or name.")
parser.add_argument("--id", type=str, help="The TMDb ID of the movie/series to search. Must be a positive integer.")
parser.add_argument("--name", type=str, nargs='+', help="The name of the movie/series to search.")
parser.add_argument("--logging", action="store_true", help="Enable logging to file.")
parser.add_argument("--debug", action="store_true", help="Enable debug level logging.")
parser.add_argument("--movies", "--m", action="store_true", help="Search for movies.")
parser.add_argument("--series", "--s", action="store_true", help="Search for TV series.")
parser.add_argument("--search", type=str, help="Search for specific terms in the name. Separate multiple terms with `^`.")
parser.add_argument("--json", action="store_true", help="Save JSON responses for each site.")
parser.add_argument("--overwrite", action="store_true", help="Overwrite the existing .env file if it exists.",)
args = parser.parse_args()

def main():
    # Setup logging for regular and debug mode
    setup_logging(OUTPUT_DIR, debug_mode=args.debug)

    # Overwrite .env with default values
    if args.overwrite:
        create_env_file(overwrite=args.overwrite)
    else:
        create_env_file() # Create .env file if one is not present
    
    # Validate environment variables
    env_vars = validate_env_vars()

    # Access required variables
    tmdb_api_key = env_vars["required"]["TMDB_API_KEY"]
    tmdb_url = env_vars["required"]["TMDB_URL"]

    # Use valid pairs
    trackers = env_vars["trackers"]
    for tracker in trackers:
        api_key = tracker["api_key"]
        url = tracker["url"]
        tracker_name = tracker["name"]
        tracker_code = tracker["code"]
        
        logging.info(f"{tracker_name} ({tracker_code}) | Using API key [REDACTED] with URL: {url}")

    search_type = "movie" if args.movies else "tv" if args.series else None
    search_query = args.search

    try:
        if not search_type:
            raise ValueError("Please specify either --movies or --series to search.")

        if args.id:
            tmdb_id = args.id.strip()
            if not tmdb_id.isdigit():
                raise ValueError("TMDb ID must be a positive integer.")
            details = search_tmdb(search_type, tmdb_api_key, tmdb_url, tmdb_id=tmdb_id)
        elif args.name:
            name = args.name
            results = search_tmdb(search_type, tmdb_api_key, tmdb_url, name=name)
            selected_result = select_tmdb_result(results)
            if selected_result:
                details = search_tmdb(search_type, tmdb_api_key, tmdb_url, tmdb_id=selected_result['id'])
            else:
                console.print("[bold yellow]No suitable result selected.[/bold yellow]")
                exit()
        else:
            raise ValueError("Please specify either --id or --name to search.")

        display_movie_details(details)
        query_additional_apis(details['id'], search_query, trackers, args.json, OUTPUT_DIR)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()