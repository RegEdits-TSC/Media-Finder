import logging
import time
from rich.table import Table
from rich.console import Console

console = Console()

def display_movie_details(details):
    """Display movie/series details."""
    try:
        table = Table(title="Movie/Series Details", title_style="bold green", border_style="bold white")
        table.add_column("Field", style="bold green", no_wrap=True)
        table.add_column("Value", style="bold yellow")

        title = details.get('title', details.get('name', 'N/A'))
        table.add_row("Title", title)
        table.add_row("Release Year", details.get('release_date', details.get('first_air_date', 'N/A'))[:4])
        table.add_row("Genres", ', '.join(genre['name'] for genre in details.get('genres', [])))
        runtime = details.get('runtime')
        if runtime:
            table.add_row("Runtime", f"{runtime // 60}h {runtime % 60}m")
        table.add_row("Overview", details.get('overview', 'No overview available.'))

        console.print(table)

        console.print(f"\n[bold yellow]Searching trackers for {title}...[/bold yellow]")
        logging.info(f"Started searching trackers for {title}.")

        time.sleep(2)
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

        table = Table(title=f"{api_name} Results", title_style="bold green", border_style="bold white")
        table.add_column("Name", style="bold yellow")
        table.add_column("Size", justify="right")
        table.add_column("Seeders", justify="center")
        table.add_column("Leechers", justify="center")
        table.add_column("Freeleech", justify="center")

        for result in data:
            attributes = result["attributes"]
            name = attributes.get("name", "N/A")
            size = f"{attributes.get('size', 0) / (1024 ** 3):.2f} GiB"
            seeders = attributes.get("seeders", 0)
            leechers = attributes.get("leechers", 0)
            freeleech = attributes.get("freeleech", "No")

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