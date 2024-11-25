import json
import logging
import os
import requests
from urllib.parse import urljoin
from utils.helpers import display_api_results
from rich.table import Table
from rich.console import Console

console = Console()

def search_tmdb(search_type, tmdb_api_key=None, tmdb_url=None, tmdb_id=None, name=None):
    """Fetch details by ID or name for movies/series."""
    try:
        if tmdb_id:
            logging.info(f"Initiating fetch for search_type: {search_type}, TMDb ID: {tmdb_id}")
            endpoint = f"{search_type}/{tmdb_id}"
            params = {"api_key": tmdb_api_key}
            return fetch_details(endpoint, params, tmdb_url=tmdb_url)
        elif name:
            logging.info(f"Initiating fetch for search_type: {search_type}, Name: {' '.join(name)}")
            endpoint = f"search/{search_type}"
            params = {"api_key": tmdb_api_key, "query": " ".join(name)}
            results = fetch_details(endpoint, params, tmdb_url=tmdb_url).get('results', [])
            if not results:
                raise ValueError(f"No results found for the name '{' '.join(name)}'.")
            return results
        else:
            raise ValueError("Invalid input: Provide either TMDb ID or name.")
    except ValueError as e:
        logging.error(f"Error in search_tmdb: {str(e)}")
        raise

def fetch_details(endpoint, params, tmdb_url=None):
    """Fetch details from TMDb API."""
    url = urljoin(tmdb_url, endpoint)
    try:
        logging.info(f"Fetching data from endpoint: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        logging.debug(f"Response data: {response.json()}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data from TMDb: {str(e)}")
        raise ValueError(f"TMDb API call failed: {str(e)}")
    
def query_additional_apis(tmdb_id, search_query=None, trackers=None, output_json=None, OUTPUT_DIR=None):
    """Query additional APIs using the TMDb ID and filter results by search query if set."""
    failed_sites = {}
    successful_sites = []
    missing_media = {}

    media_types = ["REMUX", "WEB-DL", "Encode"]

    params = {'tmdbId': tmdb_id}
    headers = {'Content-Type': 'application/json'}

    for tracker in trackers:
        api_key = tracker["api_key"]
        url = tracker["url"]
        tracker_name = tracker["name"]
        tracker_code = tracker["code"]
        if not api_key:
            reason = "Missing API key"
            logging.warning(f"Skipping {tracker_name}: {reason}")
            failed_sites[tracker_name] = reason
            continue

        headers['Authorization'] = f"Bearer {api_key}"

        try:
            if search_query:
                logging.info(f"Querying {tracker_name} for TMDb ID: {tmdb_id} with search query: {search_query}")
            else:
                logging.info(f"Querying {tracker_name} for TMDb ID: {tmdb_id}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                reason = f"Invalid JSON response: {response.text[:100]}..."
                logging.error(f"{tracker_name} API failed: {reason}")
                failed_sites[tracker_name] = "Invalid JSON response"
                continue

            if data and 'data' in data and data['data']:
                # Filter results locally if search query exists
                if search_query:
                    filtered_results = [
                        item for item in data['data']
                        if all(term.lower() in item['attributes']['name'].lower() for term in search_query.split("^"))
                    ]
                    if not filtered_results:
                        reason = f"No results matching query '{search_query}'"
                        logging.info(f"{tracker_name} returned no matching results for TMDb ID {tmdb_id}.")
                        failed_sites[tracker_name] = reason
                        continue

                    data['data'] = filtered_results

                # Check for required media types
                site_media_types = [
                    item['attributes']['type'] for item in data['data'] if 'type' in item['attributes']
                ]
                for media_type in media_types:
                    if not any(
                        media_type.lower() in item['attributes']['name'].lower() or
                        media_type.lower() == t.lower()
                        for item in data['data'] for t in site_media_types
                    ):
                        if tracker_name not in missing_media:
                            missing_media[tracker_name] = []
                        missing_media[tracker_name].append(media_type)

                # Export JSON only if --json argument is passed
                if output_json:
                    filename = os.path.join(OUTPUT_DIR, f"{tracker_code}_TMDb_{tmdb_id}.json")
                    with open(filename, "w", encoding="utf-8") as json_file:
                        json.dump(data, json_file, ensure_ascii=False, indent=4)
                    logging.info(f"Exported {tracker_name} ({tracker_code}) response to {filename}")

                display_api_results(data, tracker_name)
                successful_sites.append(tracker_name)
                logging.info(f"{tracker_name} found data for TMDb ID {tmdb_id}.")
            else:
                reason = "No matching results found"
                logging.info(f"{tracker_name} returned no data for TMDb ID {tmdb_id}.")
                failed_sites[tracker_name] = reason

        except requests.RequestException as e:
            reason = f"Request error: {str(e)}"
            logging.error(f"Error querying {tracker_name}: {reason}")
            failed_sites[tracker_name] = reason

    # Display Failed Sites Table
    if failed_sites:
        failed_table = Table(title="Failed Sites", title_style="bold red", border_style="bold white")
        failed_table.add_column("Site", style="bold yellow")
        failed_table.add_column("Reason", style="bold red")

        for site, reason in failed_sites.items():
            failed_table.add_row(site, reason)

        console.print(failed_table)


    # Display Missing Media Types Table
    if missing_media and not search_query:
        missing_table = Table(title="Missing Media Types", title_style="bold red", border_style="bold white")
        missing_table.add_column("Site", style="bold yellow")
        missing_table.add_column("Missing Media Types", style="bold red")

        for site, media_types in missing_media.items():
            missing_table.add_row(site, ", ".join(media_types))

        console.print(missing_table)

    # Display if no sites are successful
    if not successful_sites:
        console.print("[bold red]No successful queries.[/bold red]")