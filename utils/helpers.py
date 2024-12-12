import argparse
import json
import logging
from pathlib import Path
from rich.table import Table
from rich.console import Console
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import LOG_PREFIX_JSON, LOG_PREFIX_OUTPUT, LOG_PREFIX_PROCESS, LOG_PREFIX_SAVE

console = Console()

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Fetch movie/series details from TMDb using a TMDb ID or name.")
    parser.add_argument("--id", type=str, help="The TMDb ID of the movie/series to search. Must be a positive integer.")
    parser.add_argument("--name", type=str, nargs='+', help="The name of the movie/series to search.")
    parser.add_argument("--logging", action="store_true", help="Enable logging to file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug level logging.")
    parser.add_argument("--movies", "--m", action="store_true", help="Search for movies.")
    parser.add_argument("--series", "--s", action="store_true", help="Search for TV series.")
    parser.add_argument("--search", type=str, help="Search for specific terms in the name. Separate multiple terms with `^`.")
    parser.add_argument("--json", action="store_true", help="Save JSON responses for each site.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite the existing .env file if it exists.")
    return parser.parse_args()

def display_movie_details(logger: logging.Logger, details: Dict[str, Any]) -> None:
    """Display movie/series details."""
    try:
        title = details.get('title', details.get('name', 'N/A'))
        release_date = details.get('release_date', details.get('first_air_date', 'N/A'))
        genres = ', '.join(genre['name'] for genre in details.get('genres', []))
        runtime = details.get('runtime')
        overview = details.get('overview', 'No overview available.')

        # Prepare rows for the table
        rows = [
            ("Title", title),
            ("Release Year", release_date[:4]),
            ("Genres", genres),
            ("Runtime", f"{runtime // 60}h {runtime % 60}m" if runtime else "N/A"),
            ("Overview", overview)
        ]

        # Create and print the table
        table_name = "Movie/Series Details"
        columns = [("Field", "bold green", "left"), ("Details", "bold yellow", "left")]
        table = create_table(logger, table_name, columns, rows, title_style="bold green", border_style="bold white")
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying {table_name} table.")
        console.print(table)

        return title
    except KeyError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Key error displaying {table_name} table: {str(e)}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Error displaying {table_name} table: {str(e)}")

def display_api_results(logger: logging.Logger, response_data: Dict[str, Any], api_name: str, search_query: Optional[str] = None) -> None:
    """Display results from an API in a formatted table with optional search."""
    try:
        data = response_data.get("data", [])
        filtered_by_search = False

        # Filter results if a search query is provided
        if search_query:
            logger.info(f"{LOG_PREFIX_PROCESS} Filtering {api_name} results for: {search_query}")
            data = search_results(response_data, search_query)
            filtered_by_search = True

        # Skip displaying if no results are found
        if not data:
            if filtered_by_search:
                logger.info(f"{LOG_PREFIX_OUTPUT} {api_name} API Results: No matching results found for the query: {search_query}")
            else:
                logger.info(f"{LOG_PREFIX_OUTPUT} {api_name} API Results: No data found.")
            return

        # Prepare rows for the table
        rows = []
        for result in data:
            attributes = result["attributes"]
            name = attributes.get("name", "N/A")
            size = bytes_to_gib(attributes.get("size", 0))
            seeders = attributes.get("seeders", "N/A")
            leechers = attributes.get("leechers", "N/A")
            freeleech = attributes.get("freeleech", "N/A")
            rows.append((name, size, str(seeders), str(leechers), freeleech))

        # Create and print the table
        columns = [
            ("Name", "bold yellow", "left"),
            ("Size", "bold yellow", "center"),
            ("Seeders", "bold yellow", "center"),
            ("Leechers", "bold yellow", "center"),
            ("Freeleech", "bold yellow", "center")
        ]

        table_name = f"{api_name} Results"
        table = create_table(logger, table_name, columns, rows, title_style="bold green", border_style="bold white")
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying {table_name} table.")
        console.print(table)
    except KeyError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} KeyError in {table_name} table: {str(e)}")
    except TypeError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} TypeError in {table_name} table: {str(e)}")
    except ValueError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} ValueError in {table_name} table: {str(e)}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Unexpected error displaying {table_name} table: {str(e)}")

def search_results(response_data: Dict[str, Any], query: str) -> List[Any]:
    """Search for specific strings in the name of API results."""
    results = response_data.get("data", [])
    filtered_results = []

    for result in results:
        name = result["attributes"].get("name", "").lower()
        if query.lower() in name:
            filtered_results.append(result)

    return filtered_results

def bytes_to_gib(size_in_bytes: int) -> float:
    """Convert a size in bytes to a human-readable string in GiB."""
    if not size_in_bytes or size_in_bytes <= 0:
        return "0.00 GiB"
    return f"{size_in_bytes / (1024 ** 3):.2f} GiB"

def create_table(logger: logging.Logger, title: str, columns: List[Tuple[str, str, str]], rows: List[List[str]], title_style: str = "bold red", border_style: str = "bold white") -> Table:
    """Create a table with the given title, columns, and rows."""
    # Spacer for better readability
    console.print("")
    try:
        table = Table(title=title, title_style=title_style, border_style=border_style, expand=True)
        for column, style, justify in columns:
            table.add_column(column, style=style, justify=justify)
        for row in rows:
            table.add_row(*row)
        
        logger.info(f"{LOG_PREFIX_PROCESS} Created table: {title}")
        
        return table
    except Exception as e:
        logger.error(f"Failed to create {title} table: {e}")
        raise

def export_json(logger: logging.Logger, OUTPUT_DIR: str, data: Dict[str, Any], tracker_code: str, tracker_name: str, tmdb_id: str) -> None:
    """Export the data to a JSON file."""
    try:
        filename = Path(OUTPUT_DIR) / f"{tracker_code}_TMDb_{tmdb_id}.json"
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info(f"{LOG_PREFIX_SAVE} Exported {tracker_name} ({tracker_code}) data to {filename}")
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
    except IOError as e:
        logger.error(f"I/O error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def display_failed_sites(logger, failed_sites: dict[str, str]) -> None:
    """Display a table of failed sites and their reasons."""
    try:
        failed_columns = [("Site", "bold yellow", "left"), ("Reason", "bold red", "left")]
        failed_rows = [(site, reason) for site, reason in failed_sites.items()]
        failed_table = create_table(logger, "Failed Sites", failed_columns, failed_rows)
        console.print(failed_table)
    except Exception as e:
        logger.error(f"Failed to display failed sites: {e}")

def display_missing_media_types(logger, missing_media: dict[str, list[str]]) -> None:
    """Display a table of sites with missing media types."""
    try:
        missing_columns = [("Site", "bold yellow", "left"), ("Missing Media Types", "bold red", "left")]
        missing_rows = [(site, ", ".join(media_types)) for site, media_types in missing_media.items()]
        missing_table = create_table(logger, "Missing Media Types", missing_columns, missing_rows)
        console.print(missing_table)
    except Exception as e:
        logger.error(f"Failed to display missing media types: {e}")