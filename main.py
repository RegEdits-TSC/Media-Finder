import logging
from pathlib import Path
from utils.validation import setup_environment, API_KEYS
from utils.helpers import display_movie_details, parse_arguments
from utils.logger import setup_logging
from cmds.processing import select_tmdb_result
from cmds.api_commands import search_tmdb, query_additional_apis
from rich.console import Console
from utils.exceptions import MissingArgumentError, InvalidTMDbIDError, NoSuitableResultError

console = Console()

# Determine the directory of the script and the output folder
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "logs"

def setup(args):
    """Setup logging and environment variables."""
    # Setup logging with the specified output directory and debug mode
    if args.logging or args.debug:
        setup_logging(OUTPUT_DIR, debug_mode=args.debug, sensitive_values=list(API_KEYS.values()))

    # Setup environment variables, optionally overwriting existing ones
    env_vars = setup_environment(overwrite=args.overwrite)

    # Access required TMDb API key and URL from environment variables
    tmdb_api_key = env_vars["required"]["TMDB_API_KEY"]
    tmdb_url = env_vars["required"]["TMDB_URL"]

    # Retrieve valid tracker API key and URL pairs
    trackers = env_vars["trackers"]
    for tracker in trackers:
        api_key = tracker["api_key"]
        url = tracker["url"]
        tracker_name = tracker["name"]
        tracker_code = tracker["code"]
        
        # Log the tracker information
        logging.info(f"{tracker_name} ({tracker_code}) | Using provided API key with URL: {url}")

    return tmdb_api_key, tmdb_url, trackers

def perform_search(args, tmdb_api_key, tmdb_url, trackers):
    """Perform the search based on the provided arguments."""
    # Determine the search type based on the arguments
    search_type = "movie" if args.movies else "tv" if args.series else None
    search_query = args.search

    # Ensure a valid search type is specified
    if not search_type:
        raise MissingArgumentError("Please specify either --movies or --series to search.")

    # Search by TMDb ID if provided
    if args.id:
        tmdb_id = args.id.strip()
        if not tmdb_id.isdigit():
            raise InvalidTMDbIDError("TMDb ID must be a positive integer.")
        details = search_tmdb(search_type, tmdb_api_key, tmdb_url, tmdb_id=tmdb_id)
    # Search by name if provided
    elif args.name:
        name = args.name
        results = search_tmdb(search_type, tmdb_api_key, tmdb_url, name=name)
        selected_result = select_tmdb_result(results)
        if selected_result:
            details = search_tmdb(search_type, tmdb_api_key, tmdb_url, tmdb_id=selected_result['id'])
        else:
            raise NoSuitableResultError("No suitable result selected.")
    else:
        raise MissingArgumentError("Please specify either --id or --name to search.")

    # Display the movie details
    title = display_movie_details(details)
    # Query additional APIs using the TMDb ID
    query_additional_apis(details['id'], title, search_query, trackers, args.json, OUTPUT_DIR)

def handle_errors(func):
    """Decorator to handle errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MissingArgumentError as e:
            logging.error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        except InvalidTMDbIDError as e:
            logging.error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        except NoSuitableResultError as e:
            logging.error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        except ValueError as e:
            logging.error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    return wrapper

@handle_errors
def main() -> None:
    """Main function to execute the script."""
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging and environment variables
    tmdb_api_key, tmdb_url, trackers = setup(args)

    # Perform the search based on the provided arguments
    perform_search(args, tmdb_api_key, tmdb_url, trackers)

if __name__ == "__main__":
    main()