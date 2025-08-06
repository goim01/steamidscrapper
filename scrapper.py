import requests
import re
import time

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
    """Fetch Mod IDs for a list of Workshop IDs using Steam Web API."""
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    # Split into batches of 100 to respect API limits
    batch_size = 100
    mod_ids = []
    
    for i in range(0, len(workshop_ids), batch_size):
        batch = workshop_ids[i:i + batch_size]
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
                continue
                
            for item in result["response"]["publishedfiledetails"]:
                workshop_id = item["publishedfileid"]
                if item.get("result", 0) != 1:
                    print(f"Error: Could not fetch details for Workshop ID {workshop_id}")
                    mod_ids.append(f"Unknown_{workshop_id}")
                    continue
                description = item.get("description", "")
                mod_id = get_mod_id_from_description(description)
                if mod_id:
                    print(f"Workshop ID: {workshop_id} -> Mod ID: {mod_id}")
                    mod_ids.append(mod_id)
                else:
                    print(f"Workshop ID: {workshop_id} -> Mod ID: Unknown_{workshop_id}")
                    mod_ids.append(f"Unknown_{workshop_id}")
        except requests.RequestException as e:
            print(f"Error fetching batch {batch}: {e}")
            for wid in batch:
                mod_ids.append(f"Unknown_{wid}")
        time.sleep(1)  # Avoid rate limiting
    
    # Return semicolon-separated string of Mod IDs
    return ";".join(mod_ids)

# Main execution
if __name__ == "__main__":
    # Replace with your Steam Web API key
    API_KEY = "A5CEAD1D0ADA7F94BEF5F8445FFFCD1D"
    
    # Prompt user for Workshop IDs
    workshop_ids_input = input("Enter Workshop IDs (separated by ';'): ")
    workshop_ids = [wid.strip() for wid in workshop_ids_input.split(";") if wid.strip()]
    
    # Fetch and extract Mod IDs
    mod_ids_output = get_mod_ids(workshop_ids, API_KEY)
    print("\nSemicolon-separated Mod IDs:")
    print(mod_ids_output)