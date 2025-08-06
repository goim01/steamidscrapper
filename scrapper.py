import requests
import re
import sqlite3
import time

def init_database():
    """Initialize SQLite database and create mod_mappings table if it doesn't exist."""
    conn = sqlite3.connect('mod_ids.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mod_mappings (
            workshop_id TEXT PRIMARY KEY,
            mod_id TEXT
        )
    ''')
    conn.commit()
    return conn, cursor

def get_cached_mod_ids(workshop_ids, cursor):
    """Check database for cached Workshop ID to Mod ID mappings."""
    cached_mod_ids = {}
    placeholders = ','.join(['?'] * len(workshop_ids))
    cursor.execute(f'SELECT workshop_id, mod_id FROM mod_mappings WHERE workshop_id IN ({placeholders})', workshop_ids)
    for row in cursor.fetchall():
        cached_mod_ids[row[0]] = row[1]
    return cached_mod_ids

def save_mod_id(workshop_id, mod_id, cursor, conn):
    """Save a Workshop ID to Mod ID mapping to the database."""
    cursor.execute('INSERT OR REPLACE INTO mod_mappings (workshop_id, mod_id) VALUES (?, ?)', (workshop_id, mod_id))
    conn.commit()

def get_mod_id_from_description(description):
    """Extract Mod ID from a mod's description using regex."""
    if not description:
        return None
    # Common patterns for Mod ID in descriptions
    patterns = [
        r'Mod ID:\s*([^\s;]+)',
        r'Mods:\s*([^\s;]+)',
        r'ModID:\s*([^\s;]+)',
        r'mod_id:\s*([^\s;]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def get_mod_ids(workshop_ids, api_key):
    """Fetch Mod IDs for a list of Workshop IDs using Steam Web API, with caching."""
    # Initialize database
    conn, cursor = init_database()
    
    # Check for cached Mod IDs
    cached_mod_ids = get_cached_mod_ids(workshop_ids, cursor)
    mod_ids = []
    uncached_workshop_ids = [wid for wid in workshop_ids if wid not in cached_mod_ids]
    
    # Process cached results first
    for wid in workshop_ids:
        if wid in cached_mod_ids:
            mod_id = cached_mod_ids[wid]
            print(f"Workshop ID: {wid} -> Mod ID: {mod_id} (from cache)")
            mod_ids.append(mod_id)
    
    if not uncached_workshop_ids:
        conn.close()
        return ";".join(mod_ids)
    
    # Fetch details for uncached Workshop IDs
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    batch_size = 100  # Respect API limits
    
    for i in range(0, len(uncached_workshop_ids), batch_size):
        batch = uncached_workshop_ids[i:i + batch_size]
        data = {
            "itemcount": len(batch),
            "publishedfileids": batch
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data={"key": api_key, "itemcount": len(batch), **{f"publishedfileids[{j}]": wid for j, wid in enumerate(batch)}}, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if "response" not in result or "publishedfiledetails" not in result["response"]:
                print(f"Error: Invalid response for batch {batch}")
                for wid in batch:
                    mod_ids.append(f"Unknown_{wid}")
                    save_mod_id(wid, f"Unknown_{wid}", cursor, conn)
                continue
                
            for item in result["response"]["publishedfiledetails"]:
                workshop_id = item["publishedfileid"]
                if item.get("result", 0) != 1:
                    print(f"Error: Could not fetch details for Workshop ID {workshop_id}")
                    mod_ids.append(f"Unknown_{workshop_id}")
                    save_mod_id(workshop_id, f"Unknown_{workshop_id}", cursor, conn)
                    continue
                description = item.get("description", "")
                mod_id = get_mod_id_from_description(description)
                if mod_id:
                    print(f"Workshop ID: {workshop_id} -> Mod ID: {mod_id}")
                    mod_ids.append(mod_id)
                    save_mod_id(workshop_id, mod_id, cursor, conn)
                else:
                    print(f"Workshop ID: {workshop_id} -> Mod ID: Unknown_{workshop_id}")
                    mod_ids.append(f"Unknown_{workshop_id}")
                    save_mod_id(workshop_id, f"Unknown_{workshop_id}", cursor, conn)
        except requests.RequestException as e:
            print(f"Error fetching batch {batch}: {e}")
            for wid in batch:
                mod_ids.append(f"Unknown_{wid}")
                save_mod_id(wid, f"Unknown_{wid}", cursor, conn)
        time.sleep(1)  # Avoid rate limiting
    
    conn.close()
    # Return semicolon-separated string of Mod IDs
    return ";".join(mod_ids)

# Main execution
if __name__ == "__main__":
    # Replace with your Steam Web API key
    API_KEY = "YOUR_STEAM_API_KEY_HERE"
    
    # Prompt user for Workshop IDs
    workshop_ids_input = input("Enter Workshop IDs (separated by ';'): ")
    workshop_ids = [wid.strip() for wid in workshop_ids_input.split(";") if wid.strip()]
    
    # Fetch and extract Mod IDs
    mod_ids_output = get_mod_ids(workshop_ids, API_KEY)
    print("\nSemicolon-separated Mod IDs:")
    print(mod_ids_output)