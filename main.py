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

def main() -> None:
    """Main function to execute the script."""
    args = parse_arguments()

    # Setup logging
    setup_logging(OUTPUT_DIR, debug_mode=args.debug, sensitive_values=list(API_KEYS.values()))

    # Setup environment
    env_vars = setup_environment(overwrite=args.overwrite)

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
        
        logging.info(f"{tracker_name} ({tracker_code}) | Using provided API key with URL: {url}")

    search_type = "movie" if args.movies else "tv" if args.series else None
    search_query = args.search

    try:
        if not search_type:
            raise MissingArgumentError("Please specify either --movies or --series to search.")

        if args.id:
            tmdb_id = args.id.strip()
            if not tmdb_id.isdigit():
                raise InvalidTMDbIDError("TMDb ID must be a positive integer.")
            details = search_tmdb(search_type, tmdb_api_key, tmdb_url, tmdb_id=tmdb_id)
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

        display_movie_details(details)
        query_additional_apis(details['id'], search_query, trackers, args.json, OUTPUT_DIR)
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

if __name__ == "__main__":
    main()