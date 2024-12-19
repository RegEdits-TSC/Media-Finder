# Standard Library Imports
import json
import logging
import time
from pathlib import Path
from urllib.parse import urljoin
from typing import Optional, Dict, Any, List

# Third-Party Imports
import requests
from rich.console import Console

# Local Imports
from cmds.processing import check_media_types, filter_results
from utils.helpers import (
    display_api_results,
    display_failed_sites,
    display_missing_media_types,
    export_json,
)
from utils.exceptions import NoResultsFoundError
from utils.logger import (
    LOG_PREFIX_API,
    LOG_PREFIX_FETCH,
    LOG_PREFIX_JSON,
    LOG_PREFIX_OUTPUT,
    LOG_PREFIX_PROCESS,
    LOG_PREFIX_RESULT,
    LOG_PREFIX_SEARCH,
)

console = Console()

def search_tmdb(
    logger: logging.Logger,
    search_type: str,
    tmdb_api_key: Optional[str] = None,
    tmdb_url: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    name: Optional[List[str]] = None,
) -> Any:
    """
    Fetch details by ID or name for movies/series.
    Returns:
        - Single result as a dictionary when `tmdb_id` is provided.
        - List of results when `name` is provided.
    """
    try:
        # Validate essential inputs
        if not tmdb_api_key or not tmdb_url:
            raise ValueError("TMDb API key and URL must be provided.")

        if tmdb_id:
            logger.info(f"{LOG_PREFIX_FETCH} Fetching details for TMDb ID: {tmdb_id}")
            endpoint = f"{search_type}/{tmdb_id}"
            params = {"api_key": tmdb_api_key}
            return fetch_details(logger, endpoint, params, tmdb_url)

        elif name:
            query = " ".join(name)
            logger.info(f"{LOG_PREFIX_FETCH} Searching for '{query}' in '{search_type}'")
            endpoint = f"search/{search_type}"
            params = {"api_key": tmdb_api_key, "query": query}
            response = fetch_details(logger, endpoint, params, tmdb_url)
            
            results = response.get("results", [])
            if not results:
                logger.warning(f"{LOG_PREFIX_FETCH} No results found for query: {query}")
                raise NoResultsFoundError(query)

            return results

        else:
            logger.error(f"{LOG_PREFIX_FETCH} Either 'tmdb_id' or 'name' must be provided.")
            raise ValueError("You must provide either 'tmdb_id' or 'name' to search.")

    except NoResultsFoundError as e:
        query = " ".join(name) if name else "Unknown query"
        logger.error(f"{LOG_PREFIX_FETCH} No results found for query: {query}")
        console.print(f"[bold red]Error:[/bold red] No results found for '{query}'")
        raise

    except ValueError as e:
        logger.error(f"{LOG_PREFIX_FETCH} ValueError: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"{LOG_PREFIX_FETCH} Unexpected error: {str(e)}")
        raise

def fetch_details(
    logger: logging.Logger,
    endpoint: str,
    params: Dict[str, str],
    tmdb_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch details from the TMDb API.
    Returns:
        Parsed JSON response from the API.
    """
    try:
        # Validate inputs
        if not tmdb_url:
            raise ValueError("TMDb URL is required.")
        if not endpoint:
            raise ValueError("Endpoint is required.")
        if not isinstance(params, dict):
            raise ValueError("Params must be a dictionary.")

        # Construct the full URL
        url = urljoin(tmdb_url, endpoint)
        logger.info(f"{LOG_PREFIX_PROCESS} Constructed URL: {url}")

        # Make the request
        logger.info(f"{LOG_PREFIX_FETCH} Sending request to {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Parse and return the response
        try:
            data = response.json()
            logger.debug(f"{LOG_PREFIX_RESULT} API Response: {data}")
            return data
        except requests.JSONDecodeError:
            logger.error(f"{LOG_PREFIX_API} Received invalid JSON response from {url}.")
            raise ValueError("Invalid JSON response received from TMDb API.")

    except requests.Timeout:
        logger.error(f"{LOG_PREFIX_API} Request to {url} timed out.")
        raise ValueError("TMDb API request timed out.")
    except requests.RequestException as e:
        logger.error(f"{LOG_PREFIX_API} Request to {url} failed: {str(e)}")
        raise ValueError(f"TMDb API request failed: {str(e)}")
    except ValueError as e:
        logger.error(f"{LOG_PREFIX_API} Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"{LOG_PREFIX_API} Unexpected error: {str(e)}")
        raise
    
def query_tracker_api(
    logger: logging.Logger,
    tmdb_id: str,
    title: str,
    search_query: Optional[str] = None,
    trackers: Optional[List[Dict[str, str]]] = None,
    output_json: Optional[bool] = None,
    OUTPUT_DIR: Optional[Path] = None,
) -> None:
    """
    Query additional APIs using the TMDb ID and filter results by search query if applicable.
    """
    # Validate essential inputs
    if not trackers:
        logger.error(f"{LOG_PREFIX_API} No trackers provided.")
        raise ValueError("Trackers list is required.")
    if not tmdb_id:
        logger.error(f"{LOG_PREFIX_API} No TMDb ID provided.")
        raise ValueError("TMDb ID is required.")

    # Initialize tracking variables
    failed_sites = {}
    successful_sites = []
    collected_data = []
    missing_media = {}

    # Display search banner
    search_banner = (
        f"Searching trackers for {title} with search query '{search_query}'"
        if search_query
        else f"Searching trackers for {title}"
    )
    console.rule(f"[bold yellow]{search_banner}[/bold yellow]", align="center")
    logger.info(f"{LOG_PREFIX_SEARCH} {search_banner}")

    # Helper: Handle API responses
    def handle_response(tracker_name: str, response: requests.Response) -> Optional[Dict[str, Any]]:
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.error(
                f"{LOG_PREFIX_API} {tracker_name} returned invalid JSON: {response.text[:100]}..."
            )
            failed_sites[tracker_name] = "Invalid JSON response"
            return None

    # Helper: Process each tracker
    def process_tracker(tracker: Dict[str, str]) -> None:
        tracker_name = tracker.get("name", "Unknown Tracker")
        api_key = tracker.get("api_key")
        url = tracker.get("url")
        tracker_code = tracker.get("code", "")

        if not api_key or not url:
            logger.warning(f"{LOG_PREFIX_API} Skipping {tracker_name}: Missing API key or URL.")
            failed_sites[tracker_name] = "Missing API key or URL"
            return

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        params = {"tmdbId": tmdb_id}

        try:
            logger.info(f"{LOG_PREFIX_SEARCH} Querying {tracker_name} for TMDb ID: {tmdb_id}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = handle_response(tracker_name, response)
            if not data:
                logger.info(f"{LOG_PREFIX_PROCESS} {tracker_name} returned no data.")
                return

            collected_data.append((data, tracker_code, tracker_name))
            process_tracker_data(tracker_name, data)

        except requests.RequestException as e:
            logger.error(f"{LOG_PREFIX_API} Request to {tracker_name} failed: {str(e)}")
            failed_sites[tracker_name] = str(e)

    # Helper: Process tracker data
    def process_tracker_data(tracker_name: str, data: Dict[str, Any]) -> None:
        if data and "data" in data and data["data"]:
            if search_query:
                filtered_results = filter_results(logger, data, search_query)
                if not filtered_results:
                    logger.info(f"{LOG_PREFIX_PROCESS} No results matching '{search_query}' on {tracker_name}.")
                    failed_sites[tracker_name] = f"No results matching '{search_query}'"
                    return
                data["data"] = filtered_results

            if not search_query:
                check_media_types(logger, data, tracker_name, missing_media)

            display_api_results(logger, data, tracker_name)
            successful_sites.append(tracker_name)
        else:
            logger.info(f"{LOG_PREFIX_PROCESS} No matching results on {tracker_name}.")
            failed_sites[tracker_name] = "No matching results"

    # Iterate over trackers and process each
    for tracker in trackers:
        process_tracker(tracker)
        time.sleep(1)  # Avoid rate-limiting

    # Export collected data to JSON if requested
    if output_json and OUTPUT_DIR:
        logger.info(f"{LOG_PREFIX_JSON} Exporting tracker data to: {OUTPUT_DIR}")
        for data, tracker_code, tracker_name in collected_data:
            export_json(logger, OUTPUT_DIR, data, tracker_code, tracker_name, tmdb_id)

    logger.info(f"{LOG_PREFIX_PROCESS} Checking for failed sites...")

    # Display results summary
    if failed_sites:
        logger.info(f"{LOG_PREFIX_PROCESS} Gathering failed sites...")
        display_failed_sites(logger, failed_sites)
    else:
        logger.info(f"{LOG_PREFIX_PROCESS} No failed sites found.")
    
    logger.info(f"{LOG_PREFIX_PROCESS} Checking for missing media types...")

    if missing_media:
        logger.info(f"{LOG_PREFIX_PROCESS} Gathering missing media types...")
        display_missing_media_types(logger, missing_media)
    else:
        logger.info(f"{LOG_PREFIX_PROCESS} All media types found on configured sites.")

    if not successful_sites:
        logger.error(f"{LOG_PREFIX_OUTPUT} No successful queries.")
        console.print("[bold red]No successful queries.[/bold red]")