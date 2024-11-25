import argparse
import logging
import time
from rich.table import Table
from rich.console import Console
from typing import Any, Dict

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

def display_movie_details(details: Dict[str, Any]) -> None:
    """Display movie/series details."""
    try:
        table = Table(title="Movie/Series Details", title_style="bold green", border_style="bold white")
        table.add_column("Field", style="bold green", no_wrap=True)
        table.add_column("Value", style="bold yellow")

        title = details.get('title', details.get('name', 'N/A'))
        release_date = details.get('release_date', details.get('first_air_date', 'N/A'))
        genres = ', '.join(genre['name'] for genre in details.get('genres', []))
        runtime = details.get('runtime')
        overview = details.get('overview', 'No overview available.')

        table.add_row("Title", title)
        table.add_row("Release Year", release_date[:4])
        table.add_row("Genres", genres)
        if runtime:
            table.add_row("Runtime", f"{runtime // 60}h {runtime % 60}m")
        table.add_row("Overview", overview)

        console.print(table)

        console.print(f"\n[bold yellow]Searching trackers for {title}...[/bold yellow]")
        logging.info(f"Started searching trackers for {title}.")

        time.sleep(2)
    except KeyError as e:
        logging.error(f"Key error displaying movie details: {str(e)}")
    except Exception as e:
        logging.error(f"Error displaying movie details: {str(e)}")

def display_api_results(response_data, api_name, search_query=None):
    """Display results from an API in a formatted table with optional search."""
    try:
        data = response_data.get("data", [])
        
        # Filter results if a search query is provided
        if search_query:
            data = search_results(response_data, search_query)

        # Skip displaying if no results are found
        if not data:
            console.print(f"[bold red]{api_name} API Results: No matching results found.[/bold red]")
            return

        table = Table(title=f"{api_name} Results", title_style="bold green", title_justify="center", border_style="bold white")
        table.add_column("Name", style="bold yellow")
        table.add_column("Size", justify="right")
        table.add_column("Seeders", justify="center")
        table.add_column("Leechers", justify="center")
        table.add_column("Freeleech", justify="center")

        for result in data:
            attributes = result["attributes"]
            name = attributes.get("name", "N/A")
            size = bytes_to_gib(attributes.get("size", 0))
            seeders = attributes.get("seeders", "N/A")
            leechers = attributes.get("leechers", "N/A")
            freeleech = attributes.get("freeleech", "N/A")

            table.add_row(
                name,
                size,
                str(seeders),
                str(leechers),
                freeleech
            )

        console.print(table)
    except Exception as e:
        logging.error(f"Error displaying {api_name} results: {str(e)}")

def search_results(response_data, query):
    """Search for specific strings in the name of API results."""
    results = response_data.get("data", [])
    filtered_results = []

    for result in results:
        name = result["attributes"].get("name", "").lower()
        if query.lower() in name:
            filtered_results.append(result)

    return filtered_results

def bytes_to_gib(size_in_bytes):
    """Convert a size in bytes to a human-readable string in GiB."""
    if not size_in_bytes or size_in_bytes <= 0:
        return "0.00 GiB"
    return f"{size_in_bytes / (1024 ** 3):.2f} GiB"