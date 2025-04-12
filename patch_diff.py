import requests
import json
from deepdiff import DeepDiff
import os
from config import CURRENT_PATCH, PREVIOUS_PATCH

# Base URLs
BASE_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/"
CHAMPION_URL = BASE_URL + "championFull.json"
ITEM_URL = BASE_URL + "item.json"
CHAMPION_TAGS_URL = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json"

# New URLs
RUNES_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/runesReforged.json"
SUMMONER_SPELLS_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/summoner.json"

# Config
OUTPUT_DIR = "patch_diffs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_json_or_load_local(url, cache_path):
    if os.path.exists(cache_path):
        print(f"Loading cached data from {cache_path}")
        with open(cache_path, "r") as f:
            return json.load(f)
    else:
        print(f"Downloading from {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)
        return data

def download_tags_or_load_local(url, cache_path):
    if os.path.exists(cache_path):
        print(f"Loading cached champion tags from {cache_path}")
        with open(cache_path, "r") as f:
            return json.load(f)
    else:
        print(f"Downloading champion tags from {url}")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)
        return data

def get_item_mapping(patch_version):
    """Fetch item mapping from Data Dragon."""
    url = ITEM_URL.format(patch=patch_version)
    data = download_json_or_load_local(url, os.path.join(OUTPUT_DIR, f"item_mapping_{patch_version}.json"))
    items = data.get("data", {})

    item_mapping = {}
    for item_id, item_info in items.items():
        item_mapping[item_id] = item_info.get("name", f"Item {item_id}")
    return item_mapping

def get_runes_mapping(patch_version):
    """Fetch runes mapping from Data Dragon."""
    url = RUNES_URL.format(patch=patch_version)
    data = download_json_or_load_local(url, os.path.join(OUTPUT_DIR, f"runes_mapping_{patch_version}.json"))

    runes_mapping = {}
    for style in data:
        for rune in style.get("slots", []):
            for option in rune.get("runes", []):
                runes_mapping[option["id"]] = option["name"]
    return runes_mapping

def get_summoner_spells_mapping(patch_version):
    """Fetch summoner spells mapping from Data Dragon."""
    url = SUMMONER_SPELLS_URL.format(patch=patch_version)
    data = download_json_or_load_local(url, os.path.join(OUTPUT_DIR, f"summoner_spells_mapping_{patch_version}.json"))

    spells_mapping = {}
    spells = data.get("data", {})
    for spell_key, spell_info in spells.items():
        spells_mapping[int(spell_info["key"])] = spell_info["name"]
    return spells_mapping

def summarize_change(name, change, item_mapping=None, important_only=False):
    summaries = []
    spell_changes = {}
    stat_changes = []
    gameplay_updates = 0

    if "new" in change and change["new"]:
        summaries.append(f"New entity added: {item_mapping.get(name, name) if item_mapping else name}.")
    if "deleted" in change and change["deleted"]:
        summaries.append(f"Entity removed: {item_mapping.get(name, name) if item_mapping else name}.")

    pretty_name = item_mapping.get(name, name) if item_mapping else name
    if "values_changed" in change:
        for key, val in change["values_changed"].items():
            if "stats" in key:
                stat = key.split("['")[-1].split("']")[0]
                old, new = val.get("old_value"), val.get("new_value")
                if isinstance(old, (int, float)) and isinstance(new, (int, float)):
                    if old > new:
                        stat_changes.append(f"{pretty_name} {stat} decreased from {old} to {new}.")
                    else:
                        stat_changes.append(f"{pretty_name} {stat} increased from {old} to {new}.")
            elif "spells" in key and ("cooldown" in key or "effectBurn" in key or "damage" in key or "heal"):
                spell_idx = key.split("['spells'][")[-1].split("]")[0]
                stat = key.split("['")[-1].split("']")[0]
                old, new = val.get("old_value"), val.get("new_value")
                spell_changes.setdefault(spell_idx, []).append(stat)
            elif "description" in key and "spells" in key:
                # Only capture spell description if functional
                old_text, new_text = val.get("old_value", ""), val.get("new_value", "")
                if not important_only and any(word in old_text.lower() + new_text.lower() for word in ["damage", "range", "cooldown", "duration", "speed", "armor", "health", "attack"]):
                    spell_idx = key.split("['spells'][")[-1].split("]")[0]
                    summaries.append(f"{pretty_name} spell {spell_idx} description updated with functional change.")
            elif "description" in key and "root" in key:
                old_text, new_text = val.get("old_value", ""), val.get("new_value", "")
                if not important_only and any(word in old_text.lower() + new_text.lower() for word in ["damage", "speed", "armor", "health", "attack", "ability power", "cooldown"]):
                    summaries.append(f"{pretty_name} item description updated with functional change.")

    if "type_changes" in change:
        for key, val in change["type_changes"].items():
            summaries.append(f"{pretty_name} {key.split('[')[-1].split(']')[0]} type changed.")

    if "iterable_item_added" in change:
        for key, val in change["iterable_item_added"].items():
            if "skins" not in key:  # Ignore skins
                gameplay_updates += 1

    if "iterable_item_removed" in change:
        for key, val in change["iterable_item_removed"].items():
            if "skins" not in key:  # Ignore skins
                gameplay_updates += 1

    # Group repeated gameplay updates
    if gameplay_updates >= 5:
        summaries.append(f"{pretty_name} gameplay data updated.")
    elif gameplay_updates > 0:
        summaries.append(f"{pretty_name} had {gameplay_updates} gameplay-related changes.")

    # Group spell changes
    for spell_idx, stat_list in spell_changes.items():
        unique_stats = list(set(stat_list))
        spell_name = "passive" if spell_idx == "0" else f"spell {spell_idx}"
        if len(unique_stats) == 1:
            summaries.append(f"{pretty_name} {spell_name} {unique_stats[0]} changed across ranks.")
        else:
            summaries.append(f"{pretty_name} {spell_name} updated.")

    # Group stat changes
    for stat_change in stat_changes:
        summaries.append(stat_change)

    return summaries

def save_diff(diff, filename, summarized_filename=None, important_summarized_filename=None):
    if isinstance(diff, dict):
        jsonable = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in diff.items()}
    else:
        jsonable = diff.to_dict() if hasattr(diff, 'to_dict') else diff

    with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
        json.dump(jsonable, f, indent=2, default=str)

    # Save summarized version if filename provided
    if summarized_filename:
        summaries = {}
        item_mapping = get_item_mapping(CURRENT_PATCH)
        for name, change in diff.items():
            summarized = summarize_change(name, change, item_mapping=item_mapping, important_only=False)
            if summarized:
                summaries[name] = summarized

        with open(os.path.join(OUTPUT_DIR, summarized_filename), "w") as f:
            json.dump(summaries, f, indent=2)

    if important_summarized_filename:
        important_summaries = {}
        for name, change in diff.items():
            summarized = summarize_change(name, change, item_mapping=item_mapping, important_only=True)
            if summarized:
                important_summaries[name] = summarized

        with open(os.path.join(OUTPUT_DIR, important_summarized_filename), "w") as f:
            json.dump(important_summaries, f, indent=2)

def compute_patch_diff(entity_type):
    print(f"Fetching {entity_type} data...")

    # Define local cache paths
    old_cache_path = os.path.join(OUTPUT_DIR, f"{entity_type}_old_{PREVIOUS_PATCH}.json")
    new_cache_path = os.path.join(OUTPUT_DIR, f"{entity_type}_new_{CURRENT_PATCH}.json")

    # Download old and new data or load from local cache
    old_data = download_json_or_load_local((CHAMPION_URL if entity_type == "champion" else ITEM_URL).format(patch=PREVIOUS_PATCH), old_cache_path)
    new_data = download_json_or_load_local((CHAMPION_URL if entity_type == "champion" else ITEM_URL).format(patch=CURRENT_PATCH), new_cache_path)

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

    save_diff(champion_diffs, "champion_patch_diff.json", summarized_filename="champion_patch_summary.json", important_summarized_filename="champion_patch_important_summary.json")
    save_diff(item_diffs, "item_patch_diff.json", summarized_filename="item_patch_summary.json", important_summarized_filename="item_patch_important_summary.json")

    # Save item mapping separately
    item_mapping = get_item_mapping(CURRENT_PATCH)
    with open(os.path.join(OUTPUT_DIR, "item_mapping.json"), "w") as f:
        json.dump(item_mapping, f, indent=2)

    # Fetch champion tags
    champion_tags_path = os.path.join(OUTPUT_DIR, "champion_tags.json")
    champion_tags = download_tags_or_load_local(CHAMPION_TAGS_URL, champion_tags_path)
    print(f"Champion tags saved in {champion_tags_path}")

    # Save runes mapping
    runes_mapping = get_runes_mapping(CURRENT_PATCH)
    with open(os.path.join(OUTPUT_DIR, "runes_mapping.json"), "w") as f:
        json.dump(runes_mapping, f, indent=2)
    print("Runes mapping saved.")

    # Save summoner spells mapping
    summoner_spells_mapping = get_summoner_spells_mapping(CURRENT_PATCH)
    with open(os.path.join(OUTPUT_DIR, "summoner_spells_mapping.json"), "w") as f:
        json.dump(summoner_spells_mapping, f, indent=2)
    print("Summoner spells mapping saved.")

    print(f"Patch diffs saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()