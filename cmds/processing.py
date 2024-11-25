import logging
from rich.console import Console
from rich.table import Table

console = Console()

def display_results_table(results):
    """Display search results in a table."""
    # Create a table with a title and column styles
    table = Table(title="Search Results", title_style="bold green", border_style="bold white")
    table.add_column("Index", style="bold green", no_wrap=True)
    table.add_column("Title", style="bold yellow")
    table.add_column("Release Year", style="bold yellow")

    # Populate the table with results
    for index, result in enumerate(results, start=1):
        title = result.get('title', result.get('name', 'N/A'))  # Get the title or name of the result
        release_year = result.get('release_date', result.get('first_air_date', 'N/A'))[:4]  # Get the release year
        table.add_row(str(index), title, release_year)  # Add a row to the table

    # Print the table to the console
    console.print(table)

def get_user_choice(num_results):
    """Get user choice for selecting a result."""
    while True:
        # Prompt the user to enter their choice
        choice = console.input("\nEnter the index of the correct result, or type 'none' if none are correct: ").strip().lower()
        if choice == 'none':
            logging.info("User chose 'none', no result selected.")
            return None  # Return None if the user chooses 'none'
        elif choice.isdigit() and 1 <= int(choice) <= num_results:
            logging.info(f"User selected result at index: {choice}")
            return int(choice) - 1  # Return the index of the selected result
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")  # Prompt the user to try again if the input is invalid

def select_tmdb_result(results):
    """Select a result interactively."""
    try:
        logging.info(f"Processing {len(results)} search results.")
        if len(results) == 1:
            # Automatically select the result if there is only one
            selected = results[0]
            console.print(f"[bold yellow]Automatically selected:[/bold yellow] {selected.get('title', 'N/A')}")
            logging.info(f"Automatically selected result: {selected}")
            return selected

        # Display results in a table for user selection
        display_results_table(results)

        # Get user choice
        choice_index = get_user_choice(len(results))
        return results[choice_index] if choice_index is not None else None  # Return the selected result or None

    except Exception as e:
        logging.error(f"Error in select_tmdb_result: {str(e)}")
        raise  # Re-raise the exception after logging the error