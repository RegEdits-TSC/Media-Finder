# Standard library imports
import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Third-party library imports
from rich.console import Console
from rich.table import Table

# Local imports
from utils.logger import (
    LOG_PREFIX_JSON,
    LOG_PREFIX_OUTPUT,
    LOG_PREFIX_PROCESS,
    LOG_PREFIX_SAVE,
)

console = Console()

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Fetch movie/series details from TMDb using a TMDb ID or name."
    )

    # Argument definitions
    parser.add_argument(
        "--id",
        type=str,
        help="The TMDb ID of the movie/series to search. Must be a positive integer."
    )
    parser.add_argument(
        "--name",
        type=str,
        nargs='+',
        help="The name of the movie/series to search."
    )
    parser.add_argument(
        "--logging",
        action="store_true",
        help="Enable logging to file."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug level logging."
    )
    parser.add_argument(
        "--movies",
        "--m",
        action="store_true",
        help="Search for movies."
    )
    parser.add_argument(
        "--series",
        "--s",
        action="store_true",
        help="Search for TV series."
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search for specific terms in the name. Separate multiple terms with `^`."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Save JSON responses for each site."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing .env file if it exists."
    )
    parser.add_argument(
        "--type",
        type=validate_media_type,
        help="Search for only the specific media type.",
    )

    return parser.parse_args()

def validate_media_type(value: str) -> str:
    """
    Validate and normalize the media type.

    Args:
        value (str): The media type input from the user.

    Returns:
        str: The validated media type in its canonical form.

    Raises:
        argparse.ArgumentTypeError: If the input is not a valid media type.
    """
    # Define allowed types and their canonical forms
    allowed_types = {
        "remux": "Remux",
        "web-dl": "WEB-DL",
        "encode": "Encode",
        "full disc": "Full Disc",
        "webrip": "WEBRip",
        "hdtv": "HDTV",
    }

    # Normalize input for validation
    value_lower = value.lower()
    if value_lower not in allowed_types:
        raise argparse.ArgumentTypeError(
            f"Invalid media type: {value}. Allowed types are: {', '.join(allowed_types.values())}"
        )

    # Return the canonical form
    return allowed_types[value_lower]

def display_movie_details(logger: logging.Logger, details: Dict[str, Any]) -> Optional[str]:
    """
    Display movie/series details in a table.
    Returns:
        Optional[str]: The title of the movie/series if available, otherwise None.
    """
    try:
        # Extract details with fallbacks
        title = details.get("title", details.get("name", "N/A"))
        release_date = details.get("release_date", details.get("first_air_date", "N/A"))
        genres = ", ".join(genre.get("name", "Unknown") for genre in details.get("genres", []))
        runtime = details.get("runtime", None)
        overview = details.get("overview", "No overview available.")

        # Format runtime
        formatted_runtime = (
            f"{runtime // 60}h {runtime % 60}m" if runtime else "N/A"
        )

        # Prepare rows for the table
        rows = [
            ("Title", title),
            ("Release Year", release_date[:4]),
            ("Genres", genres),
            ("Runtime", formatted_runtime),
            ("Overview", overview),
        ]

        # Define table properties
        table_name = "Movie/Series Details"
        columns = [("Field", "bold green", "left"), ("Details", "bold yellow", "left")]

        # Create and display the table
        table = create_table(
            logger,
            title=table_name,
            columns=columns,
            rows=rows,
            title_style="bold green",
            border_style="bold white"
        )
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying {table_name} table.")
        console.print(table)

        return title

    except KeyError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} KeyError displaying {table_name} table: {str(e)}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Unexpected error displaying {table_name} table: {str(e)}")
        raise

def display_api_results(
    logger: logging.Logger,
    response_data: Dict[str, Any],
    api_name: str,
    search_query: Optional[str] = None
) -> None:
    """
    Display results from an API in a formatted table.
    """
    try:
        # Extract results data
        data = response_data.get("data", [])
        filtered_by_search = False

        # Filter results if a search query is provided
        if search_query:
            logger.info(f"{LOG_PREFIX_PROCESS} Filtering {api_name} results for: {search_query}")
            data = search_results(logger, response_data, search_query)
            filtered_by_search = True

        # Skip displaying if no results are found
        if not data:
            message = (
                f"No matching results found for the query: {search_query}"
                if filtered_by_search
                else "No data found."
            )
            logger.info(f"{LOG_PREFIX_OUTPUT} {api_name} API Results: {message}")
            return

        # Prepare rows for the table
        rows = [
            (
                result["attributes"].get("name", "N/A"),
                bytes_to_gib(logger, result["attributes"].get("size", 0)),
                str(result["attributes"].get("seeders", "N/A")),
                str(result["attributes"].get("leechers", "N/A")),
                result["attributes"].get("freeleech", "N/A"),
            )
            for result in data
        ]

        # Define table properties
        columns = [
            ("Name", "bold yellow", "left"),
            ("Size", "bold yellow", "center"),
            ("Seeders", "bold yellow", "center"),
            ("Leechers", "bold yellow", "center"),
            ("Freeleech", "bold yellow", "center"),
        ]

        table_name = f"{api_name} Results"
        table = create_table(
            logger,
            title=table_name,
            columns=columns,
            rows=rows,
            title_style="bold green",
            border_style="bold white",
        )

        # Log and display the table
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying {table_name} table.")
        console.print(table)

    except KeyError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} KeyError in {api_name} table: {e}")
    except TypeError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} TypeError in {api_name} table: {e}")
    except ValueError as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} ValueError in {api_name} table: {e}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Unexpected error displaying {api_name} table: {e}")
        raise

def search_results(logger: logging.Logger, response_data: Dict[str, Any], query: str) -> List[Any]:
    """
    Search for specific strings in the 'name' attribute of API results.
    Returns:
        List[Any]: A list of filtered results where the query matches the 'name'.
    """
    try:
        # Extract data and filter results
        results = response_data.get("data", [])
        query_lower = query.lower()

        filtered_results = [
            result for result in results
            if query_lower in result["attributes"].get("name", "").lower()
        ]

        return filtered_results

    except KeyError as e:
        # Handle cases where 'attributes' or 'name' keys are missing
        logger.error(f"{LOG_PREFIX_PROCESS} KeyError during search: {e}")
        return []

    except Exception as e:
        # Log unexpected errors
        logger.error(f"{LOG_PREFIX_PROCESS} Unexpected error during search: {e}")
        return []

def bytes_to_gib(logger: logging.Logger, size_in_bytes: Optional[int]) -> str:
    """
    Convert a size in bytes to a human-readable string in GiB.
    Returns:
        str: Size in GiB formatted to two decimal places.
    """
    try:
        # Validate input and handle invalid or missing values
        if not isinstance(size_in_bytes, int) or size_in_bytes <= 0:
            return "0.00 GiB"

        # Convert bytes to GiB with precision
        gib = size_in_bytes / (1024 ** 3)
        return f"{gib:.2f} GiB"

    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} Error converting bytes to GiB: {e}")
        return "0.00 GiB"

def create_table(
    logger: logging.Logger,
    title: str,
    columns: List[Tuple[str, str, str]],
    rows: List[List[str]],
    title_style: str = "bold red",
    border_style: str = "bold white",
) -> Table:
    """
    Create a table with the given title, columns, and rows.
    Returns:
        Table: A formatted rich table ready for display.
    """
    # Add a spacer for better readability
    console.print("")
    try:
        # Initialize the table with given styles
        table = Table(title=title, title_style=title_style, border_style=border_style, expand=True)

        # Add columns to the table
        for column_name, style, justify in columns:
            table.add_column(column_name, style=style, justify=justify)

        # Add rows to the table
        for row in rows:
            table.add_row(*row)

        # Log table creation
        logger.info(f"{LOG_PREFIX_PROCESS} Created table: {title}")

        return table

    except Exception as e:
        # Log and re-raise any unexpected exceptions
        logger.error(f"{LOG_PREFIX_PROCESS} Failed to create table '{title}': {e}")
        raise

def export_json(
    logger: logging.Logger,
    output_dir: str,
    data: Dict[str, Any],
    tracker_code: str,
    tracker_name: str,
    tmdb_id: str,
) -> None:
    """
    Export the given data to a JSON file.
    """
    try:
        # Construct the filename
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = output_path / f"{tracker_code}_TMDb_{tmdb_id}.json"

        # Write the data to the JSON file
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        # Log successful export
        logger.info(f"{LOG_PREFIX_SAVE} Exported {tracker_name} ({tracker_code}) data to {filename}")

    except FileNotFoundError as e:
        logger.error(f"{LOG_PREFIX_JSON} FileNotFoundError during export: {e}")

    except IOError as e:
        logger.error(f"{LOG_PREFIX_JSON} IOError during export: {e}")

    except Exception as e:
        logger.error(f"{LOG_PREFIX_JSON} Unexpected error during export: {e}")

def display_failed_sites(logger: logging.Logger, failed_sites: Dict[str, str]) -> None:
    """
    Display a table of failed sites and their reasons.
    """
    try:
        # Define columns for the table
        columns = [("Site", "bold yellow", "left"), ("Reason", "bold red", "left")]

        # Prepare rows from the failed_sites dictionary
        rows = [(site, reason) for site, reason in failed_sites.items()]

        # Create and display the table
        table = create_table(logger, title="Failed Sites", columns=columns, rows=rows, title_style="bold red")
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying failed sites table.")
        console.print(table)

    except Exception as e:
        # Log any unexpected errors
        logger.error(f"{LOG_PREFIX_OUTPUT} Failed to display failed sites: {e}")

def display_missing_media_types(logger: logging.Logger, missing_media: Dict[str, List[str]]) -> None:
    """
    Display a table of sites with missing media types.
    """
    try:
        # Define columns for the table
        columns = [("Site", "bold yellow", "left"), ("Missing Media Types", "bold red", "left")]

        # Prepare rows from the missing_media dictionary
        rows = [(site, ", ".join(media_types)) for site, media_types in missing_media.items()]

        # Create and display the table
        table = create_table(logger, title="Missing Media Types", columns=columns, rows=rows, title_style="bold red")
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying missing media types table.")
        console.print(table)

    except Exception as e:
        # Log any unexpected errors
        logger.error(f"{LOG_PREFIX_OUTPUT} Failed to display missing media types: {e}")