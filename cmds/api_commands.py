import json
import logging
from pathlib import Path
import time
import requests
from urllib.parse import urljoin
from cmds.processing import check_media_types, filter_results
from utils.helpers import create_table, display_api_results, display_failed_sites, display_missing_media_types, export_json
from rich.console import Console
from typing import Optional, Dict, Any, List
from utils.exceptions import NoResultsFoundError
from utils.logger import LOG_PREFIX_API, LOG_PREFIX_FETCH, LOG_PREFIX_JSON, LOG_PREFIX_OUTPUT, LOG_PREFIX_PROCESS, LOG_PREFIX_RESULT, LOG_PREFIX_SEARCH

console = Console()

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
        logger.error(f"{LOG_PREFIX_FETCH} TMDb: No results found for {' '.join(name)}")
        raise

def fetch_details(logger: logging.Logger, endpoint: str, params: Dict[str, str], tmdb_url: Optional[str] = None) -> Dict[str, Any]:
    """Fetch details from TMDb API."""
    logger.info(f"{LOG_PREFIX_PROCESS} Joining TMDb URL with endpoint: {endpoint}")
    url = urljoin(tmdb_url, endpoint)

    try:
        logger.info(f"{LOG_PREFIX_FETCH} Fetching data from: {url}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        logger.debug(f"{LOG_PREFIX_RESULT} Response data: {response.json()}")
        return response.json()
    except requests.Timeout:
        logger.error(f"{LOG_PREFIX_API} Request to TMDb API timed out.")
        raise ValueError("TMDb API call timed out.")
    except requests.RequestException as e:
        logger.error(f"{LOG_PREFIX_API} Failed to fetch data from TMDb: {str(e)}")
        raise ValueError(f"TMDb API call failed: {str(e)}")
    
def query_tracker_api(logger: logging.Logger, tmdb_id: str, title: str, search_query: Optional[str] = None, trackers: Optional[List[dict]] = None, output_json: Optional[bool] = None, OUTPUT_DIR: Optional[Path] = None) -> None:
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
            logger.error(f"{LOG_PREFIX_API} {tracker_name} API failed: {reason}")
            failed_sites[tracker_name] = "Invalid JSON response"
            return None
        return data

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
                filtered_by_search = False

                if search_query:
                    # Filter results if search query is provided
                    filtered_results = filter_results(logger, data, search_query)
                    if not filtered_results:
                        reason = f"No results matching query: '{search_query}'"
                        logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} failed: {reason}")
                        failed_sites[tracker_name] = reason
                        filtered_by_search = True
                    else:
                        data['data'] = filtered_results

                if not filtered_by_search:
                    logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} found data for TMDb ID {tmdb_id}")

                    # Check for missing media types if there is not a search query
                    if not search_query:
                        missing_media = check_media_types(logger, data, tracker_name, missing_media)
                    else:
                        logger.info(f"{LOG_PREFIX_PROCESS} Skipping missing media type check for {tracker_name} due to search query.")

                    # Display the API results in the console
                    display_api_results(logger, data, tracker_name)
                    successful_sites.append(tracker_name)
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
        logger.info(f"{LOG_PREFIX_JSON} Exporting tracker data to: {OUTPUT_DIR}")
        for data, tracker_code, tracker_name in collected_data:
            # Export data to JSON if JSON args is set
            export_json(logger, OUTPUT_DIR, data, tracker_code, tracker_name, tmdb_id)

    if failed_sites:
        display_failed_sites(logger, failed_sites)
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying failed sites")
    
    if missing_media:
        display_missing_media_types(logger, missing_media)
        logger.info(f"{LOG_PREFIX_OUTPUT} Displaying sites with missing media types")

    if not successful_sites:
        logger.error(f"{LOG_PREFIX_OUTPUT} No successful queries.")
        # Print a message if no successful queries were made
        console.print("[bold red]No successful queries.[/bold red]")