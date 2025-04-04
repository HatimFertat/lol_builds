import requests
import json
from deepdiff import DeepDiff
import os

# Base URLs
BASE_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/"
CHAMPION_URL = BASE_URL + "championFull.json"
ITEM_URL = BASE_URL + "item.json"

# Config
CURRENT_PATCH = "15.7.1"  # Set manually for now
PREVIOUS_PATCH = "15.6.1"  # Set manually for now
OUTPUT_DIR = "patch_diffs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_json(url):
    print(url)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

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

    print(f"Patch diffs saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()