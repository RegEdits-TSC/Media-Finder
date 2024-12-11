# Media-Finder

Media-Finder is a Python-based tool designed to streamline the process of searching, querying, and managing media information. It integrates with various APIs (e.g., TMDb, UNIT3D trackers) to provide detailed media metadata and tracker-specific results. This tool is highly customizable and supports .env configuration for secure API key management.

> [!CAUTION]
> This script is currently in its beta/testing phase and is continuously evolving. If you encounter any errors or issues while using it, please don’t hesitate to reach out or open a pull request. Contributions and feedback are always appreciated.

![License](https://img.shields.io/github/license/RegEdits-TSC/Media-Finder) ![Issues](https://img.shields.io/github/issues/RegEdits-TSC/Media-Finder) ![Stars](https://img.shields.io/github/stars/RegEdits-TSC/Media-Finder) ![Forks](https://img.shields.io/github/forks/RegEdits-TSC/Media-Finder)

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Example Usage](#example-usage)
- [Features in Development](#features-in-development)
- [Contributing](#contributing)
- [License](#license)
- [Additional Notes](#additional-notes)

## Features
- **TMDb Integration:** Fetch detailed metadata for movies and TV series using TMDb.
- **Tracker API Support:** Query multiple trackers (Aither, Upload.cx, FearNoPeer, etc.) with flexible search options.
- **Rich Logging and Output:** Uses the rich library for colorful and detailed console output.
- **Dynamic .env Creation:** Generate a .env file with preset keys for easy configuration.
- **Secure API Key Handling:** Keep sensitive values hidden with environment-based configuration.
- **CLI Integration:** Includes a command-line interface for ease of use and automation

## Requirements
- Python 3.9+
- **Libraries:** Install required Python packages using pip install -r requirements.txt.

## Installation
**1) Clone the repository:**
```bash
git clone https://github.com/RegEdits-TSC/Media-Finder.git
cd Media-Finder
```

**2) Install dependencies:**
```bash
pip install -r requirements.txt
```

**3) Create a configuration file:**
```bash
python main.py
```

**4) Edit the .env file located in the config/ directory with your API keys and URLs:**
```
TMDB_API_KEY=<your_tmdb_api_key>
TMDB_URL=https://api.themoviedb.org/3/

ATH_API_KEY=<your_ath_api_key>
ATH_URL=https://aither.cc/api/torrents/filter

# Repeat for other trackers
```

## Usage
### CLI Options
**General Options:**
- Create or Overwrite .env File:
  - `--overwrite`: Overwrites the existing .env file if it already exists.
```bash
python main.py --env [--overwrite]
```
> [!NOTE]
> If a `.env` file is not detected when the script is executed, a default configuration file will be automatically generated in the `/config` directory.

- Enable Logging:
  - `--logging`: Enables logging to a file for easier debugging.
  - `--debug`: Enables detailed debug-level logging. (This should only be utilized if troubleshooting assistance is required.)
```bash
python main.py --logging
```

**Media Search Options:**
> [!CAUTION]
> Since searches rely primarily on the TMDb API and the ID it provides based on the query, improper TMDb IDs assigned to a movie or series by the tracker may lead to unexpected results. Similarly, if a TMDb ID is not set, the search will return "No matching results found."

- Search by TMDb ID:
  - `--id`: Specify the TMDb ID of the movie or series to search.
```bash
python main.py --id 12345
```

- Search by Name:
  - `--name`: Search by the name of the movie or series.
```bash
python main.py --name "Inception"
```

- Search by Terms:
  - `--search`: Search for specific terms in the name. Separate multiple terms with `^`.
```bash
python main.py --search "2160p^FLUX"
```

- Search for Movies:
  - `--movies` or `--m`: Specify that the search is for movies.
```bash
python main.py --movies
```

- Search for TV Series:
  - `--series` or `--s`: Specify that the search is for TV series.
```bash
python main.py --series
```

**JSON Handling:**
- Save JSON Responses:
  - `--json`: Save JSON responses from API queries for each site.
```bash
python main.py --json
```

### Example Usage
**Search for a Movie by Name:**
```bash
python main.py --movies --name Godzilla King of the Monsters --search "2160p^Framestor"
```
1) **Selection Menu:** If only one result is available, it will be automatically selected, and the script will proceed with processing.

![Selection Menu](https://github.com/RegEdits-TSC/Media-Finder/blob/main/imgs/Selection_Menu.png)

2) **Search Results:** If matches are found for your query, they will be displayed as follows.

![Search Results](https://github.com/RegEdits-TSC/Media-Finder/blob/main/imgs/Search_Results.png)

3) **Failed Sites:** Any sites that encounter errors during processing will be listed here, along with the corresponding failure reasons.

![Failed Sites](https://github.com/RegEdits-TSC/Media-Finder/blob/main/imgs/Failed_Sites.png)

4) **Missing Media Types:** This section will only appear when the `--search` feature is not utilized. It will display a table listing any missing media types along with their corresponding site names.

![Missing Media Types](https://github.com/RegEdits-TSC/Media-Finder/blob/main/imgs/Missing_Media_Types.png)

> [!IMPORTANT]
> The `--movies` or `--series` argument, along with either `--name` or `--id`, is required. At least one from each category must be specified; otherwise, the script will return an error and terminate.

## Configuration
**All API keys and URLs are managed via the .env file. Below is a template for your .env:**
```
# TMDb API Key
TMDB_API_KEY=<your_tmdb_api_key>

# TMDb Site URL
TMDB_URL=https://api.themoviedb.org/3/

# Site API Keys
ATH_API_KEY=<your_ath_api_key>
BLU_API_KEY=<your_blu_api_key>
FNP_API_KEY=<your_fnp_api_key>
HDB_API_KEY=<your_hdb_api_key>
LST_API_KEY=<your_lst_api_key>
OTW_API_KEY=<your_otw_api_key>
PSS_API_KEY=<your_pss_api_key>
RFX_API_KEY=<your_rfx_api_key>
ULCX_API_KEY=<your_ulcx_api_key>

# Site URLs
ATH_URL=https://aither.cc/api/torrents/filter
BLU_URL=https://blutopia.cc/api/torrents/filter
FNP_URL=https://fearnopeer.com/api/torrents/filter
HDB_URL=https://hdbits.org/api/torrents/filter
LST_URL=https://lst.gg/api/torrents/filter
OTW_URL=https://oldtoons.world/api/torrents/filter
PSS_URL=https://privatesilverscreen.cc/api/torrents/filter
RFX_URL=https://reelflix.xyz/api/torrents/filter
ULCX_URL=https://upload.cx/api/torrents/filter
```

## Features in Development
- **Enhanced API Error Handling:** More detailed messages for API failures.
- **Tracker Filtering:** Ability to filter results by specific trackers.
- **Asynchronous Processing:** Parallel API requests for improved performance.

## Contributing
**Contributions are welcome! Please follow these steps:**

1) Fork the repository.
2) Create a new branch:
```bash
git checkout -b feature-name
```
3) Commit changes and push:
```bash
git commit -m "Add new feature"
git push origin feature-name
```
4) Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/RegEdits-TSC/Media-Finder/blob/main/LICENSE) file for details.

---

### Additional Notes

- Ensure you follow the API usage guidelines of the supported torrent sites to avoid rate limiting or being banned.
- The script is designed to be user-friendly, with prompts and feedback to guide you through the search process.

![RegEdits Torrenting](https://img1.imgoe.download/hpvgg.gif)

Copyright © 2024 - RegEdits Torrenting 
