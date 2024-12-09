import json
import logging
from pathlib import Path
import time
import requests
from urllib.parse import urljoin
from utils.helpers import create_table, display_api_results
from rich.console import Console
from typing import Optional, Dict, Any, List
from utils.exceptions import NoResultsFoundError
from utils.logger import LOG_PREFIX_API, LOG_PREFIX_FETCH, LOG_PREFIX_JSON, LOG_PREFIX_PROCESS, LOG_PREFIX_RESULT, LOG_PREFIX_SAVE, LOG_PREFIX_SEARCH

console = Console()

# Define media types
MEDIA_TYPES = ["REMUX", "WEB-DL", "Encode", "Full Disc", "WEBip"]

def search_tmdb(logger: logging.Logger, search_type: str, tmdb_api_key: Optional[str] = None, tmdb_url: Optional[str] = None, tmdb_id: Optional[str] = None, name: Optional[List[str]] = None) -> Any:
    """Fetch details by ID or name for movies/series."""
    try:
        if tmdb_id:
            logger.info(f"{LOG_PREFIX_FETCH} Initiating fetch for Search Type {search_type}, TMDb ID: {tmdb_id}")
            endpoint = f"{search_type}/{tmdb_id}"
            params = {"api_key": tmdb_api_key}
            return fetch_details(logger, endpoint, params, tmdb_url=tmdb_url)
        elif name:
            logger.info(f"{LOG_PREFIX_FETCH} Initiating fetch for Search Type {search_type}, Name: {' '.join(name)}")
            endpoint = f"search/{search_type}"
            params = {"api_key": tmdb_api_key, "query": " ".join(name)}
            results = fetch_details(logger, endpoint, params, tmdb_url=tmdb_url).get('results', [])
            if not results:
                raise NoResultsFoundError(name)
            return results
    except (NoResultsFoundError) as e:
        console.print(f"[bold red]Error:[/bold red] No results found for {' '.join(name)}")
        logger.error(f"{LOG_PREFIX_FETCH} TMDb Error: {str(e)}")
        raise

def fetch_details(logger: logging.Logger, endpoint: str, params: Dict[str, str], tmdb_url: Optional[str] = None) -> Dict[str, Any]:
    """Fetch details from TMDb API."""
    url = urljoin(tmdb_url, endpoint)

    try:
        logger.info(f"{LOG_PREFIX_FETCH} Fetching data from endpoint: {url}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        logger.debug(f"{LOG_PREFIX_RESULT} Response data: {response.json()}")
        return response.json()
    except requests.Timeout:
        logger.error(f"{LOG_PREFIX_FETCH} Request to TMDb API timed out.")
        raise ValueError("TMDb API call timed out.")
    except requests.RequestException as e:
        logger.error(f"{LOG_PREFIX_FETCH} Failed to fetch data from TMDb: {str(e)}")
        raise ValueError(f"TMDb API call failed: {str(e)}")
    
def query_additional_apis(logger: logging.Logger, tmdb_id: str, title: str, search_query: Optional[str] = None, trackers: Optional[List[dict]] = None, output_json: Optional[bool] = None, OUTPUT_DIR: Optional[Path] = None) -> None:
    """Query additional APIs using the TMDb ID and filter results by search query if set."""
    # Initialize dictionaries and lists to track failed sites, successful sites, and missing media types
    failed_sites = {}
    successful_sites = []
    collected_data = []
    missing_media = {}
    params = {'tmdbId': tmdb_id}
    headers = {'Content-Type': 'application/json'}

    if search_query is not None:
        console.print("")
        console.rule(f"[bold yellow]Searching trackers for {title} with search query \"{search_query}\"...[/bold yellow]", align="center")
        console.print("")
        logger.info(f"{LOG_PREFIX_SEARCH} Started searching trackers for {title} with search query: {search_query}")
    else:
        console.print("")
        console.rule(f"[bold yellow]Searching trackers for {title}...[/bold yellow]", align="center")
        console.print("")
        logger.info(f"{LOG_PREFIX_SEARCH} Started searching trackers for {title}")

    time.sleep(1)

    def handle_response(logger: logging.Logger, tracker_name, response):
        """Handle the API response, returning the data if valid, otherwise logging an error."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            reason = f"Invalid JSON response: {response.text[:100]}..."
            logger.error(f"{LOG_PREFIX_SEARCH} {tracker_name} API failed: {reason}")
            failed_sites[tracker_name] = "Invalid JSON response"
            return None
        return data

    def filter_results(data, search_query):
        """Filter the results based on the search query."""
        return [
            item for item in data['data']
            if all(term.lower() in item['attributes']['name'].lower() for term in search_query.split("^"))
        ]

    def check_media_types(data, tracker_name):
        """Check for missing media types in the results."""
        site_media_types = [item['attributes']['type'] for item in data['data'] if 'type' in item['attributes']]
        for media_type in MEDIA_TYPES:
            if not any(
                media_type.lower() in item['attributes']['name'].lower() or
                media_type.lower() == t.lower()
                for item in data['data'] for t in site_media_types
            ):
                if tracker_name not in missing_media:
                    missing_media[tracker_name] = []
                missing_media[tracker_name].append(media_type)

    def export_json(logger: logging.Logger, data, tracker_code, tracker_name):
        """Export the data to a JSON file."""
        try:
            filename = Path(OUTPUT_DIR) / f"{tracker_code}_TMDb_{tmdb_id}.json"
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            logger.info(f"{LOG_PREFIX_SAVE} Exported {tracker_name} ({tracker_code}) response to {filename}")
        except FileNotFoundError as e:
            logger.error(f"{LOG_PREFIX_JSON} File not found error: {e}")
        except IOError as e:
            logger.error(f"{LOG_PREFIX_JSON} I/O error: {e}")
        except Exception as e:
            logger.error(f"{LOG_PREFIX_JSON} An unexpected error occurred: {e}")

    if output_json:
        logger.info(f"{LOG_PREFIX_JSON} JSON arguments detected; JSON files will be saved accordingly.")

    for tracker in trackers:
        # Extract tracker details
        api_key = tracker["api_key"]
        url = tracker["url"]
        tracker_name = tracker["name"]
        tracker_code = tracker["code"]
        if not api_key:
            # Log and continue if API key is missing
            reason = "Missing API key"
            logger.warning(f"{LOG_PREFIX_API} Skipping {tracker_name}: {reason}")
            failed_sites[tracker_name] = reason
            continue

        headers['Authorization'] = f"Bearer {api_key}"

        try:
            # Log the query attempt with the API key redacted
            logger.info(f"{LOG_PREFIX_SEARCH} Querying {tracker_name} for TMDb ID: {tmdb_id}" + (f" with search query: {search_query}" if search_query else ""))
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = handle_response(logger, tracker_name, response)
            if data is None:
                logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} returned no data.")
                continue

            collected_data.append((data, tracker_code, tracker_name))

            if data and 'data' in data and data['data']:
                if search_query:
                    # Filter results if search query is provided
                    filtered_results = filter_results(data, search_query)
                    if not filtered_results:
                        reason = f"No results matching query '{search_query}'"
                        logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} failed: {reason}")
                        failed_sites[tracker_name] = reason
                        continue
                    data['data'] = filtered_results

                # Check for missing media types
                check_media_types(data, tracker_name)

                # Display the API results in the console
                display_api_results(logger, data, tracker_name)
                successful_sites.append(tracker_name)
                logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} found data for TMDb ID {tmdb_id}")
            else:
                # Log and continue if no matching results are found
                reason = "No matching results"
                logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} failed: {reason}")
                failed_sites[tracker_name] = reason

        except requests.RequestException as e:
            # Log the exception with the API key redacted
            logger.error(f"{LOG_PREFIX_API} Request to {tracker_name} failed: {str(e)}")

        time.sleep(1)  # Add a delay to prevent rate limiting

    if output_json:
        for data, tracker_code, tracker_name in collected_data:
            # Export data to JSON if JSON args is set
            export_json(data, tracker_code, tracker_name)

    if failed_sites:
        # Create a table to display failed sites and their reasons
        failed_columns = [("Site", "bold yellow", "left"), ("Reason", "bold red", "left")]
        failed_rows = [(site, reason) for site, reason in failed_sites.items()]
        failed_table = create_table("Failed Sites", failed_columns, failed_rows)
        console.print(failed_table)

    if missing_media and not search_query:
        # Create a table to display sites with missing media types
        missing_columns = [("Site", "bold yellow", "left"), ("Missing Media Types", "bold red", "left")]
        missing_rows = [(site, ", ".join(media_types)) for site, media_types in missing_media.items()]
        missing_table = create_table("Missing Media Types", missing_columns, missing_rows)
        console.print(missing_table)

    if not successful_sites:
        # Print a message if no successful queries were made
        console.print("[bold red]No successful queries.[/bold red]")