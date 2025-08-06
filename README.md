# Steam Workshop Mod ID Fetcher for Project Zomboid

This Python script fetches Mod IDs for Project Zomboid mods from the Steam Workshop using user-provided Workshop IDs. It leverages the Steam Web API to retrieve mod details and extracts the Mod ID from each mod's description using regular expressions. To optimize performance and minimize API calls, results are cached in an SQLite database (`mod_ids.db`). The script is particularly useful for Project Zomboid server administrators who need Mod IDs for server configuration files (e.g., `servertest.ini`).

## Features

- **Fetches Mod IDs**: Retrieves Mod IDs from Steam Workshop mod descriptions based on provided Workshop IDs.
- **Database Caching**: Stores Workshop ID to Mod ID mappings in an SQLite database to avoid redundant API calls.
- **Batch Processing**: Handles API requests in batches of 100 to respect Steam Web API rate limits.
- **Error Handling**: Manages API errors and invalid responses gracefully, ensuring robust operation.
- **Server-Friendly Output**: Produces a semicolon-separated list of Mod IDs for easy integration into Project Zomboid server configurations.

## Installation

1. **Python**: Ensure you have Python 3.x installed. You can download it from [python.org](https://www.python.org/downloads/).
2. **Dependencies**: Install the required Python library using pip:
   ```bash
   pip install requests
   ```
   The `sqlite3` module is included in Python’s standard library, so no additional installation is needed.
3. **Steam Web API Key**: Obtain a key from [Steam Community](https://steamcommunity.com/dev/apikey). You must be logged into a Steam account to register for a key.

## Usage

1. **Run the Script**:
   Save the script as `get_mod_ids.py` and run it using:
   ```bash
   python get_mod_ids.py
   ```
2. **Input Workshop IDs**: When prompted, enter a semicolon-separated list of Steam Workshop IDs for Project Zomboid mods.
   Example:
   ```
   Enter Workshop IDs (separated by ';'): 2685168362;2619072426;3022543997
   ```
3. **Output**: The script will:
   - Check the SQLite database for cached results.
   - Query the Steam Web API for any uncached Workshop IDs.
   - Extract Mod IDs from mod descriptions.
   - Display each Workshop ID with its corresponding Mod ID (or `Unknown_<WorkshopID>` if not found).
   - Output a semicolon-separated list of Mod IDs.
   Example output:
   ```
   Workshop ID: 2685168362 -> Mod ID: AdvancedVolumeEnabler
   Workshop ID: 2619072426 -> Mod ID: LitSortOGSN_gold
   Workshop ID: 3022543997 -> Mod ID: modoptions
   
   Semicolon-separated Mod IDs:
   AdvancedVolumeEnabler;LitSortOGSN_gold;modoptions
   ```
   If a Workshop ID is already cached, it will show:
   ```
   Workshop ID: 2685168362 -> Mod ID: AdvancedVolumeEnabler (from cache)
   ```

## Configuration

- **Steam Web API Key**: Open `get_mod_ids.py` and replace `"YOUR_STEAM_API_KEY_HERE"` with your actual Steam Web API key. For example:
  ```python
  API_KEY = "ABC123DEF456GHI789"
  ```
- **Database**: The script automatically creates and uses `mod_ids.db` in the same directory to cache results. No additional configuration is needed.

## Using the Output

The semicolon-separated list of Mod IDs can be used directly in the `Mods=` line of your Project Zomboid server configuration file (`servertest.ini`). For example:
```ini
Mods=AdvancedVolumeEnabler;LitSortOGSN_gold;modoptions
WorkshopItems=2685168362;2619072426;3022543997
```

For any entries listed as `Unknown_<WorkshopID>`, you will need to manually determine the Mod ID:

1. Visit the Steam Workshop page: `https://steamcommunity.com/sharedfiles/filedetails/?id=<WorkshopID>`
2. Check the description or comments for the Mod ID (e.g., `Mod ID: <name>`).
3. If not found, download the mod via Steam and locate the `mod.info` file in:
   ```
   C:\Program Files (x86)\Steam\steamapps\workshop\content\108600\<WorkshopID>\mods\<ModName>\mod.info
   ```
   The Mod ID is specified in the `id=` field.
4. Replace `Unknown_<WorkshopID>` with the actual Mod ID in your configuration.

## Database

- **File**: `mod_ids.db` is created in the script’s directory.
- **Table**: `mod_mappings` with columns:
  - `workshop_id` (TEXT, PRIMARY KEY): The Steam Workshop ID (e.g., `2685168362`).
  - `mod_id` (TEXT): The Mod ID (e.g., `AdvancedVolumeEnabler`) or `Unknown_<WorkshopID>` if not found.
- **Behavior**: The script checks the database before making API calls and stores new results using `INSERT OR REPLACE` to update existing entries if needed.
- **Management**: To reset the database, delete `mod_ids.db`. The script will recreate it on the next run.

## Limitations

- **Description Dependency**: The script relies on Mod IDs being explicitly listed in the mod’s description (e.g., `Mod ID: <name>`). If the Mod ID is not present, it outputs `Unknown_<WorkshopID>`, requiring manual verification.
- **API Rate Limits**: The Steam Web API has rate limits (typically 100,000 calls per day with short-term restrictions). The script processes Workshop IDs in batches of 100 with a 1-second delay to mitigate this. If rate limit errors occur, increase the `time.sleep(1)` value in the script.
- **Regex Accuracy**: The script uses regex patterns to extract Mod IDs. If authors use unconventional formats, the Mod ID may be missed. You can extend the `get_mod_id_from_description` function with additional patterns.
- **Scope Limitation**: The script only processes user-provided Workshop IDs. To fetch Mod IDs for all Project Zomboid mods, you would need to query a Workshop collection or all mods for App ID 108600 using additional API calls (e.g., `GetCollectionDetails`).

## Dependencies

| Library | Purpose | Installation |
|---------|---------|--------------|
| `requests` | Makes HTTP requests to the Steam Web API | `pip install requests` |
| `sqlite3` | Manages the SQLite database for caching | Included in Python standard library |
| `re` | Parses Mod IDs from descriptions using regex | Included in Python standard library |
| `time` | Adds delays to avoid API rate limits | Included in Python standard library |

## Additional Notes

- **Extending Regex Patterns**: If Mod IDs are missed due to non-standard description formats, modify the `get_mod_id_from_description` function to include additional regex patterns.
- **Workshop Collections**: To process all mods in a Steam Workshop collection, you can extend the script to use the `GetCollectionDetails` API endpoint to retrieve Workshop IDs.
- **PZModScraper Integration**: For broader searches, consider using tools like `PZModScraper` (available on GitHub) to pre-fetch Mod IDs, then use this script for verification.
- **Error Handling**: The script handles API errors and invalid responses by marking affected Workshop IDs as `Unknown_<WorkshopID>` and caching this result to avoid repeated failures.

## Example Workflow for Server Setup

1. Collect Workshop IDs from your subscribed mods or a Steam Workshop collection.
2. Run the script and input the Workshop IDs.
3. Use the output Mod IDs in the `Mods=` line of `servertest.ini`.
4. Add the input Workshop IDs to the `WorkshopItems=` line.
5. For any `Unknown_<WorkshopID>` entries, manually find the Mod ID and update the configuration.
6. Test your server to ensure all mods load correctly.