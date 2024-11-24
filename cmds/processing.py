import logging
from rich.console import Console
from rich.table import Table

console = Console()

def select_tmdb_result(results):
    """Select a result interactively."""
    try:
        logging.info(f"Processing {len(results)} search results.")
        if len(results) == 1:
            selected = results[0]
            console.print(f"[bold yellow]Automatically selected:[/bold yellow] {selected.get('title', 'N/A')}")
            logging.info(f"Automatically selected result: {selected}")
            return selected

        # Display results in a table for user selection
        table = Table(title="Search Results", title_style="bold green", border_style="bold white")
        table.add_column("Index", style="bold green", no_wrap=True)
        table.add_column("Title", style="bold yellow")
        table.add_column("Release Year", style="bold yellow")

        for index, result in enumerate(results, start=1):
            title = result.get('title', result.get('name', 'N/A'))
            release_year = result.get('release_date', result.get('first_air_date', 'N/A'))[:4]
            table.add_row(str(index), title, release_year)

        console.print(table)

        while True:
            choice = console.input("\nEnter the index of the correct result, or type 'none' if none are correct: ").strip().lower()
            if choice == 'none':
                logging.info("User chose 'none', no result selected.")
                return None
            elif choice.isdigit() and 1 <= int(choice) <= len(results):
                logging.info(f"User selected result at index: {choice}")
                return results[int(choice) - 1]
            else:
                console.print("[bold red]Invalid choice. Please try again.[/bold red]")
    except Exception as e:
        logging.error(f"Error in select_tmdb_result: {str(e)}")
        raise