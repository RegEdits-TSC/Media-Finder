import logging
import sys
from rich.console import Console
from rich.table import Table
from utils.exceptions import NoResultsError, InvalidChoiceError
from utils.helpers import create_table
from utils.logger import LOG_PREFIX_INPUT, LOG_PREFIX_PROCESS

console = Console()

def display_results_table(results):
    """Display search results in a table."""
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
    table = create_table(title="Search Results", title_style="bold green", border_style="bold white", columns=columns, rows=rows)
    console.print(table)

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
        display_results_table(results)

        # Get user choice
        choice_index = get_user_choice(logger, len(results))
        if choice_index is None:
            console.print("[bold yellow]If you're confident that the media exists on TMDb, please verify the spelling of the title.[/bold yellow]")
            console.print("[bold yellow]TMDb's search functionality considers original, translated, and alternative titles, but accurate spelling ensures optimal search results.[/bold yellow]")
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