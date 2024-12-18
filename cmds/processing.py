# Standard Library Imports
import logging
import sys
from typing import Any, Dict, List, Optional

# Third-Party Imports
from rich.console import Console

# Local Imports
from utils.exceptions import InvalidChoiceError, NoResultsError
from utils.helpers import create_table
from utils.logger import (
    LOG_PREFIX_INPUT,
    LOG_PREFIX_OUTPUT,
    LOG_PREFIX_PROCESS,
    LOG_PREFIX_SEARCH,
)

console = Console()

def display_results_table(logger: logging.Logger, results: List[Dict[str, str]]) -> None:
    """Display search results in a table."""
    table_name = "Search Results"

    try:
        # Validate input
        if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
            raise TypeError("Results must be a list of dictionaries.")

        # Define table columns
        columns = [
            ("Index", "bold green", "center"),
            ("Title", "bold yellow", "left"),
            ("Release Year", "bold yellow", "center"),
        ]

        # Populate rows
        rows = []
        for index, result in enumerate(results, start=1):
            # Safely extract the title and release year
            title = result.get("title", result.get("name", "N/A"))
            release_date = result.get("release_date", result.get("first_air_date", "N/A"))
            release_year = release_date[:4] if release_date != "N/A" else "N/A"
            rows.append([str(index), title, release_year])

        # Create and display the table
        table = create_table(
            logger=logger,
            title=table_name,
            columns=columns,
            rows=rows,
            title_style="bold green",
            border_style="bold white",
        )
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying {table_name} table.")
        console.print(table)

    except Exception as e:
        logger.error(f"{LOG_PREFIX_OUTPUT} Error displaying {table_name} table: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] Failed to display the table.")
        sys.exit(1)

def get_user_choice(logger: logging.Logger, num_results: int) -> Optional[int]:
    """
    Prompt the user to select a result or choose 'none' if no result is correct.
    Returns:
        The zero-based index of the selected result, or None if the user chooses 'none'.
    """
    while True:
        # Prompt the user for input
        choice = console.input(
            "\nEnter the index of the correct result, or type 'none' if none are correct: "
        ).strip().lower()

        # Handle the 'none' option
        if choice == "none":
            logger.info(f"{LOG_PREFIX_INPUT} User chose 'none', no result selected.")
            return None

        # Handle numeric input within the valid range
        if choice.isdigit():
            choice_int = int(choice)
            if 1 <= choice_int <= num_results:
                logger.info(f"{LOG_PREFIX_INPUT} User selected result at index: {choice}")
                return choice_int - 1  # Convert to zero-based index

        # If input is invalid, show an error message and loop again
        console.print("[bold red]Invalid choice. Please enter a valid index or 'none'.[/bold red]")

def select_tmdb_result(logger: logging.Logger, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select a TMDb result interactively.
    Returns:
        The selected result as a dictionary, or None if the user selects 'none'.
    """
    try:
        # Handle empty results
        if not results:
            raise NoResultsError("No results to process.")

        logger.info(f"{LOG_PREFIX_PROCESS} Processing {len(results)} search results.")

        # Automatically select the only result
        if len(results) == 1:
            selected = results[0]
            title = selected.get("title", selected.get("name", "N/A"))
            console.print(f"[bold yellow]Automatically selected:[/bold yellow] {title}")
            logger.info(f"{LOG_PREFIX_PROCESS} Automatically selected result: {selected}")
            return selected

        # Display results for user selection
        display_results_table(logger, results)

        # Get the user's choice
        choice_index = get_user_choice(logger, len(results))
        if choice_index is None:
            console.print(
                "\n[bold yellow]If you're confident the media exists on TMDb, please double-check the title's spelling for accuracy.[/bold yellow]"
            )
            console.print(
                "[bold yellow]TMDb searches across original, translated, and alternative titles, but precise spelling helps achieve the best results.[/bold yellow]"
            )
            console.print(
                "[bold yellow]Alternatively, you can use the `--id` option if you know the entry exists on TMDb.[/bold yellow]"
            )
            logger.info(f"{LOG_PREFIX_INPUT} User chose 'none', exiting script.")
            sys.exit(0)  # Exit gracefully if the user selects 'none'

        # Validate the user's choice and return the selected result
        if 0 <= choice_index < len(results):
            selected = results[choice_index]
            logger.info(f"{LOG_PREFIX_INPUT} User selected result: {selected}")
            return selected
        else:
            raise InvalidChoiceError(f"Choice {choice_index} is out of range.")

    except NoResultsError as e:
        logger.error(f"{LOG_PREFIX_PROCESS} {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except InvalidChoiceError as e:
        logger.error(f"{LOG_PREFIX_INPUT} {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} Unexpected error: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] Unexpected error occurred.")
        raise

def check_media_types(
    logger: logging.Logger, 
    data: Dict[str, Any], 
    tracker_name: str, 
    missing_media: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Check for missing media types in the results.
    Returns:
        Updated dictionary of missing media types.
    """
    # Define media type categories and their synonyms
    MEDIA_TYPES = {
        "REMUX": {"remux"},
        "WEB-DL": {"web-dl"},
        "Encode": {"encode", "x264 encode", "x265 encode"},
        "Full Disc": {"full disc", "full disk"},
        "WEBRip": {"webrip", "web-rip"},
        "HDTV": {"hdtv"},
    }

    try:
        # Log start of the media type check process
        logger.info(f"{LOG_PREFIX_PROCESS} Checking missing media types for {tracker_name}...")

        # Extract media types found on the tracker
        site_media_types = [
            item["attributes"]["type"].lower()
            for item in data.get("data", [])
            if "type" in item.get("attributes", {})
        ]

        # Log and track unknown media types
        all_synonyms = {synonym for synonyms in MEDIA_TYPES.values() for synonym in synonyms}
        unknown_media_types = set(site_media_types) - all_synonyms
        if unknown_media_types:
            logger.warning(f"{LOG_PREFIX_PROCESS} Unknown media types on {tracker_name}: {unknown_media_types}")

        # Determine found categories based on synonyms
        found_categories = set()
        for site_type in site_media_types:
            for category, synonyms in MEDIA_TYPES.items():
                if site_type in synonyms or any(synonym in site_type for synonym in synonyms):
                    found_categories.add(category)

        # Identify missing media types
        for category in MEDIA_TYPES.keys():
            if category not in found_categories:
                missing_media.setdefault(tracker_name, []).append(category)
                logger.info(f"{LOG_PREFIX_PROCESS} Media type '{category}' not found on {tracker_name}")

        return missing_media

    except KeyError as e:
        logger.error(f"{LOG_PREFIX_PROCESS} KeyError encountered while processing {tracker_name}: {e}")
        return missing_media

    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} Unexpected error while processing {tracker_name}: {e}")
        return missing_media   

def filter_results(logger: logging.Logger, data: Dict[str, Any], search_query: str) -> List[Dict[str, Any]]:
    """
    Filter the results based on the search query.
    Returns:
        A list of filtered results matching the search query.
    """
    try:
        # Parse search query terms
        terms = [term.strip().lower() for term in search_query.split("^")]

        # Filter results
        results = [
            item for item in data.get("data", [])
            if all(term in item.get("attributes", {}).get("name", "").lower() for term in terms)
        ]

        logger.info(f"{LOG_PREFIX_SEARCH} Filtered {len(results)} result(s) based on query: {search_query}")
        return results

    except KeyError as e:
        logger.error(f"{LOG_PREFIX_SEARCH} KeyError while filtering results: {e}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_SEARCH} Unexpected error during filtering: {e}")

    return []  # Return an empty list if an exception occurs