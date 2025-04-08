import requests
import json
from deepdiff import DeepDiff
import os
from config import CURRENT_PATCH, PREVIOUS_PATCH

# Base URLs
BASE_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/"
CHAMPION_URL = BASE_URL + "championFull.json"
ITEM_URL = BASE_URL + "item.json"

# Config
OUTPUT_DIR = "patch_diffs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_json(url):
    print(url)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_item_mapping(patch_version):
    """Fetch item mapping from Data Dragon."""
    url = ITEM_URL.format(patch=patch_version)
    data = download_json(url)
    items = data.get("data", {})
    
    item_mapping = {}
    for item_id, item_info in items.items():
        item_mapping[int(item_id)] = {
            "name": item_info.get("name"),
            "description": item_info.get("description"),
            "plaintext": item_info.get("plaintext")
        }
    return item_mapping

def save_diff(diff, filename):
    if isinstance(diff, dict):
        jsonable = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in diff.items()}
    else:
        jsonable = diff.to_dict() if hasattr(diff, 'to_dict') else diff

    with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
        json.dump(jsonable, f, indent=2, default=str)

def compute_patch_diff(entity_type):
    print(f"Fetching {entity_type} data...")

    # Download old and new data
    old_data = download_json((CHAMPION_URL if entity_type == "champion" else ITEM_URL).format(patch=PREVIOUS_PATCH))
    new_data = download_json((CHAMPION_URL if entity_type == "champion" else ITEM_URL).format(patch=CURRENT_PATCH))

    # Focus only on the 'data' field
    old_entities = old_data["data"]
    new_entities = new_data["data"]

    diffs = {}

    for name in new_entities.keys():
        if name in old_entities:
            diff = DeepDiff(old_entities[name], new_entities[name], ignore_order=True)
            if diff:
                diffs[name] = diff
        else:
            diffs[name] = {"new": True}  # New entity added

    for name in old_entities.keys():
        if name not in new_entities:
            diffs[name] = {"deleted": True}  # Entity removed

    return diffs

def main():
    champion_diffs = compute_patch_diff("champion")
    item_diffs = compute_patch_diff("item")

    save_diff(champion_diffs, "champion_patch_diff.json")
    save_diff(item_diffs, "item_patch_diff.json")

    # Save item mapping separately
    item_mapping = get_item_mapping(CURRENT_PATCH)
    with open(os.path.join(OUTPUT_DIR, "item_mapping.json"), "w") as f:
        json.dump(item_mapping, f, indent=2)
    print(f"Item mapping saved in {OUTPUT_DIR}/item_mapping.json")

    print(f"Patch diffs saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()