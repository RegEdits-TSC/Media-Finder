import logging
import sys
from typing import Any, Dict, List
from rich.console import Console
from utils.exceptions import NoResultsError, InvalidChoiceError
from utils.helpers import create_table
from utils.logger import LOG_PREFIX_INPUT, LOG_PREFIX_OUTPUT, LOG_PREFIX_PROCESS, LOG_PREFIX_SEARCH

console = Console()

def display_results_table(logger: logging.Logger, results: List[Dict[str, str]]) -> None:
    """Display search results in a table."""
    try:
        # Define the columns
        columns = [
            ("Index", "bold green", "center"),
            ("Title", "bold yellow", "left"),
            ("Release Year", "bold yellow", "center")
        ]

        # Populate the rows with results
        rows = []
        for index, result in enumerate(results, start=1):
            title = result.get('title', result.get('name', 'N/A'))  # Get the title or name of the result
            release_year = result.get('release_date', result.get('first_air_date', 'N/A'))[:4]  # Get the release year
            rows.append([str(index), title, release_year])  # Add a row to the rows list

        # Create and display the table
        table_name = "Search Results"
        table = create_table(logger, title="Search Results", title_style="bold green", border_style="bold white", columns=columns, rows=rows)
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

def get_user_choice(logger: logging.Logger, num_results):
    """Get user choice for selecting a result."""
    while True:
        # Prompt the user to enter their choice
        choice = console.input("\nEnter the index of the correct result, or type 'none' if none are correct: ").strip().lower()
        if choice == 'none':
            logger.info(f"{LOG_PREFIX_INPUT} User chose 'none', no result selected.")
            return None  # Return None if the user chooses 'none'
        elif choice.isdigit() and 1 <= int(choice) <= num_results:
            logger.info(f"{LOG_PREFIX_INPUT} User selected result at index: {choice}")
            return int(choice) - 1  # Return the index of the selected result
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")  # Prompt the user to try again if the input is invalid

def select_tmdb_result(logger: logging.Logger, results):
    """Select a result interactively."""
    try:
        if not results:
            raise NoResultsError("No results to process.")

        logger.info(f"{LOG_PREFIX_PROCESS} Processing {len(results)} search results.")
        if len(results) == 1:
            # Automatically select the result if there is only one
            selected = results[0]
            console.print(f"[bold yellow]Automatically selected:[/bold yellow] {selected.get('title', 'N/A')}")
            logger.info(f"{LOG_PREFIX_PROCESS} Automatically selected result: {selected}")
            return selected

        # Display results in a table for user selection
        display_results_table(logger, results)

        # Get user choice
        choice_index = get_user_choice(logger, len(results))
        if choice_index is None:
            console.print("[bold yellow]If you're confident the media exists on TMDb, please double-check the title's spelling for accuracy.[/bold yellow]")
            console.print("[bold yellow]TMDb searches across original, translated, and alternative titles, but precise spelling helps achieve the best results.[/bold yellow]")
            console.print("[bold yellow]Alternatively, you can use the `--id` option if you know the entry exists on TMDb.[/bold yellow]")
            sys.exit(0)  # Cleanly exit the script if choice is None
        if choice_index < 0 or choice_index >= len(results):
            raise InvalidChoiceError("Invalid choice made by the user.")
        return results[choice_index]  # Return the selected result

    except NoResultsError as e:
        logger.error(f"{LOG_PREFIX_PROCESS} {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except InvalidChoiceError as e:
        logger.error(f"{LOG_PREFIX_INPUT} {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

def check_media_types(logger: logging.Logger, data: Dict[str, Any], tracker_name: str, missing_media) -> Dict[str, List[str]]:
    """Check for missing media types in the results."""
    # Define media types
    MEDIA_TYPES = {
        "REMUX": {"remux"},
        "WEB-DL": {"web-dl"},
        "Encode": {"encode", "x264 encode", "x265 encode"},
        "Full Disc": {"full disc", "full disk"},
        "WEBip": {"webip"},
        "HDTV": {"hdtv"}
    }

    try:
            # Log start of process
            logger.info(f"{LOG_PREFIX_PROCESS} Checking missing media types for {tracker_name}...")

            # Extract all media types found on the tracker site
            site_media_types = [
                item['attributes']['type'].lower()
                for item in data['data']
                if 'type' in item['attributes']
            ]

            # Track and log unknown media types
            unknown_media_types = set(site_media_types) - set(
                synonym for synonyms in MEDIA_TYPES.values() for synonym in synonyms
            )
            if unknown_media_types:
                logger.warning(f"{LOG_PREFIX_PROCESS} Unknown media types on {tracker_name}: {unknown_media_types}")

            # Normalize media types into categories
            found_categories = set()
            for site_type in site_media_types:
                for category, synonyms in MEDIA_TYPES.items():
                    if site_type in synonyms or any(synonym in site_type for synonym in synonyms):
                        found_categories.add(category)

            # Check for missing media types
            for category in MEDIA_TYPES.keys():
                if category not in found_categories:
                    if tracker_name not in missing_media:
                        missing_media[tracker_name] = []
                    missing_media[tracker_name].append(category)
                    logger.info(f"{LOG_PREFIX_PROCESS} Media type '{category}' not found on {tracker_name}")

            return missing_media
    except KeyError as e:
        logger.error(f"{LOG_PREFIX_PROCESS} KeyError: {e}")
    except Exception as e:
        logger.error(f"{LOG_PREFIX_PROCESS} An unexpected error occurred: {e}")    

def filter_results(logger: logging.Logger, data: Dict[str, Any], search_query: str) -> List[Dict[str, Any]]:
    """Filter the results based on the search query."""
    try:
        terms = search_query.lower().split("^")
        return [
            item for item in data.get('data', [])
            if all(term in item['attributes'].get('name', '').lower() for term in terms)
        ]
    except KeyError as e:
        logger.error(f"{LOG_PREFIX_SEARCH} KeyError: {e}")
        return []
    except Exception as e:
        logger.error(f"{LOG_PREFIX_SEARCH} An unexpected error occurred: {e}")
        return []