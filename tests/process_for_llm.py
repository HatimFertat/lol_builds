import sqlite3
import pandas as pd
import json
import ast
import csv
# from src.core.pipeline.config import CURRENT_PATCH
CURRENT_PATCH = "15.7.1"
#CLI: export PYTHONPATH=/home/hatim/data/sourcegit/lol_builds

DATABASE_PATH = "data/matches.db"
OUTPUT_PATH = "data/llm_ready_dataset.csv"

def format_timestamp_ms(ms):
    """Format milliseconds to mm:ss, rounding to nearest 15-second interval."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    # Round seconds to nearest 15
    rounded_seconds = int(round(seconds / 15.0) * 15)

    # Handle if we round up to 60
    if rounded_seconds == 60:
        minutes += 1
        rounded_seconds = 0

    return f"{minutes:02}:{rounded_seconds:02}"

def load_data():
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql_query("SELECT * FROM match_records", conn)
    conn.close()
    return df

def flatten_items_by_phase(item_list, item_mapping, recipe_mapping, full_item_data, match_id=None):
    """Convert a list of item events into three strings: early, mid, late, handling buys and sells properly."""
    if isinstance(item_list, str):
        item_list = ast.literal_eval(item_list)

    # Sort events by timestamp
    item_list.sort(key=lambda x: x['timestamp'])

    phases = {"early": [], "mid": [], "late": []}

    # Helper to record an action plus an inventory snapshot for the given phase
    def _log_action(phase_key: str, description: str):
        if phase_key not in phases:
            return
        phases[phase_key].append(description)
        inv_names = [
            item_mapping.get(iid)
            for iid in current_inventory
            if iid not in excluded_items and item_mapping.get(iid)
        ]
        count = len(inv_names)
        phases[phase_key].append(
            f"Inventory ({count}): " + ", ".join(inv_names) if inv_names else "Inventory (0): (empty)"
        )
        phases[phase_key].append("")

    # IDs for consumable potions and wards to exclude and elixirs
    excluded_items = {2003, 2031, 2033, 2055, 2056, 3364, 3340, 2010, 2138, 2139, 2140,
                       2150, 2151, 2152, 3363, 2003, 3364, 2055}
    # Map base item → evolved item using specialRecipe
    support_evolutions = {
        int(v["specialRecipe"]): int(k)
        for k, v in full_item_data.items()
        if "specialRecipe" in v
    }
    from functools import lru_cache
    @lru_cache(maxsize=None)
    def _basic_components(itm_id: int):
        subs = recipe_mapping.get(itm_id, [])
        if not subs:
            return [itm_id]
        comps = [itm_id]  # include the component itself
        for cid in subs:
            comps.extend(_basic_components(cid))
        return comps

    inventory_stack = []
    current_inventory = []
    recently_destroyed = []

    for event in item_list:
        item_id = event.get('itemId')
        action_raw = event.get('action', '')
        phase = event.get('phase', '')
        timestamp = event.get('timestamp', 0)
        #print(f"Processing event: {action_raw} {item_id} at {timestamp}")
        # print(action_raw, 'avant')
        # Special handling for support item evolution (quest completion) after ITEM_DESTROYED
        # (We need to look ahead to see if the next event is a support item evolution.)
        if action_raw == "ITEM_DESTROYED":
            recently_destroyed.append((item_id, timestamp))
            if item_id in current_inventory:
                current_inventory.remove(item_id)

            # Check if it's a jungle item (consumed, not evolved)
            jungle_items = {1101, 1102, 1103}  # Add others as needed
            if item_id in jungle_items:
                _log_action(phase, "Jungle quest finished")
                continue

            # Check if this item evolves via specialRecipe
            if item_id in support_evolutions:
                evolved_id = support_evolutions[item_id]
                if evolved_id not in current_inventory:
                    current_inventory.append(evolved_id)
                    base_name = item_mapping.get(item_id, f"Unknown{item_id}")
                    evolved_name = item_mapping.get(evolved_id, f"Unknown{evolved_id}")
                    _log_action(phase, f"Support item evolved from {base_name} to {evolved_name}")
            continue

        if action_raw == "ITEM_PURCHASED":
            recipe_components = recipe_mapping.get(item_id, [])
            basic_components = _basic_components(item_id)  # all leaf modules

            # Combine current inventory with items destroyed very recently (acts as a short‑lived buffer for fusions).
            inventory_and_recent = current_inventory + [
                comp_id for comp_id, comp_time in recently_destroyed
                if timestamp - comp_time <= 1000
            ]

            # A build is possible when the item has recipe components and at least one of them is available
            # either in the current inventory OR in the short‑lived destroyed buffer.
            has_any_component = any(comp in inventory_and_recent for comp in basic_components)
            can_build = bool(recipe_components) and has_any_component

            #print(f"Recipe components for {item_id}: {recipe_components}")
            #print(f"Can build {item_id}? {can_build}")
            if recipe_components and can_build:
                # Helpers for recursive component removal
                def _pop_from_sources(target_id):
                    # Try inventory first
                    if target_id in current_inventory:
                        current_inventory.remove(target_id)
                        return True
                    # Then recently destroyed buffer
                    for idx, (rid, rtime) in enumerate(recently_destroyed):
                        if rid == target_id and timestamp - rtime <= 1000:
                            recently_destroyed.pop(idx)
                            return True
                    return False

                def _consume_recursively(item_id):
                    # Remove item or recurse into its sub-components
                    if _pop_from_sources(item_id):
                        return
                    for sub in recipe_mapping.get(item_id, []):
                        _consume_recursively(sub)

                # Remove components (including nested) for this build
                for comp_id in recipe_components:
                    _consume_recursively(comp_id)
                inventory_stack.append(("Build", item_id, phase, recipe_components))
                current_inventory.append(item_id)
                #print(f"Action taken: Build {item_id}")
                #print(f"Current inventory after action: {current_inventory}")
                # Log the build event chronologically
                item_name = item_mapping.get(item_id, f"Unknown{item_id}")
                component_names = [
                    item_mapping.get(comp_id, f"Unknown{comp_id}")
                    for comp_id in recipe_components
                    if comp_id not in excluded_items
                ]
                build_desc = (
                    f"Build {item_name} (fusing {' + '.join(component_names)})"
                    if component_names
                    else f"Build {item_name}"
                )
                if item_id not in excluded_items:
                    _log_action(phase, build_desc)
            else:
                inventory_stack.append(("Buy", item_id, phase))
                current_inventory.append(item_id)
                #print(f"Action taken: Buy {item_id}")
                #print(f"Current inventory after action: {current_inventory}")
                # Log the buy event
                item_name = item_mapping.get(item_id, f"Unknown{item_id}")
                if item_id not in excluded_items:
                    _log_action(phase, f"Buy {item_name}")
        elif action_raw == "ITEM_SOLD":
            inventory_stack.append(("Sell", item_id, phase))
            if item_id in current_inventory:
                current_inventory.remove(item_id)
            #print(f"Item sold: {item_id}, Current inventory: {current_inventory}")
            item_name = item_mapping.get(item_id, f"Unknown{item_id}")
            if item_id not in excluded_items:
                _log_action(phase, f"Sell {item_name}")
        elif action_raw == "ITEM_UNDO":
            # print('hehe undo')
            if inventory_stack:
                last_action = inventory_stack.pop()
                last_action_type, last_item_id, *_ = last_action
                if last_action_type == "Buy":
                    if last_item_id in current_inventory:
                        current_inventory.remove(last_item_id)
                elif last_action_type == "Sell":
                    current_inventory.append(last_item_id)
                elif last_action_type == "Build":
                    if last_item_id in current_inventory:
                        current_inventory.remove(last_item_id)

        # print(action_raw, 'apres')
    early = "\n".join(phases["early"])
    mid = "\n".join(phases["mid"])
    late = "\n".join(phases["late"]) 

    # final_inventory_list = ", ".join(item_mapping.get(iid, f"Unknown{iid}") for iid in current_inventory)
    end_inventory_list = [item_mapping.get(iid, f"Unknown{iid}") for iid in current_inventory if iid not in excluded_items]
    # if len(end_inventory_list) > 6: print(len(end_inventory_list)) # DEBUG
    if match_id == 'NA1_5259409600' and 'World Atlas' in end_inventory_list:
        print(f"[DEBUG] Match ID: {match_id}")
        to_print = []
        #print by mapping item id to name and keep the timestamp and action fields
        for event in item_list:
            item_name = item_mapping.get(event.get('itemId'), f"Unknown{event.get('itemId')}")
            timestamp = event.get('timestamp', 0)
            to_print.append({'item_name': item_name, 'action': event.get('action', ''), 'phase': event.get('phase', ''), 'timestamp': (timestamp)})
            # to_print.append({'itemId': event.get('itemId'), 'action': event.get('action', 'caca'), 'phase': event.get('phase', ''), 'timestamp': (timestamp)})
            print(to_print[-1])

    final_inventory_list = ", ".join(end_inventory_list) if end_inventory_list else "No items."
        
    return early, mid, late, final_inventory_list

def load_champion_tags():
    """Load champion roles from file."""
    with open("patch_diffs/champion_tags.json", "r") as f:
        tag_data = json.load(f)

    # Build name -> roles mapping
    name_to_roles = {}
    for champ in tag_data:
        name = champ["name"].strip().title()
        roles = champ.get("roles", [])
        name_to_roles[name] = roles
    return name_to_roles

def format_champion_with_roles(name, roles, lane):
    """Format champion name with roles, dynamically excluding 'Support' unless played in SUPPORT lane."""
    if not roles:
        return name
    processed_roles = []
    for role in roles:
        if role.lower() == "support":
            if lane == "SUPPORT" or "SUPPORT" in lane:
                processed_roles.append(role)
        else:
            processed_roles.append(role)
    if not processed_roles:
        return name
    role_str = "/".join(processed_roles)
    return f"{name} ({role_str})"

def load_runes_and_spells():
    """Load rune and summoner spell mappings from files."""
    with open("patch_diffs/runes_mapping.json", "r") as f:
        runes_mapping = json.load(f)
        runes_mapping = {int(k): v for k, v in runes_mapping.items()}
    with open("patch_diffs/summoner_spells_mapping.json", "r") as f:
        spells_mapping = json.load(f)
        spells_mapping = {int(k): v for k, v in spells_mapping.items()}
    return runes_mapping, spells_mapping

def map_runes(rune_list, runes_mapping):
    """Map rune IDs to names."""
    if isinstance(rune_list, str):
        rune_list = ast.literal_eval(rune_list)
    return [runes_mapping.get(rune_id, f"UnknownRune{rune_id}") for rune_id in rune_list]

def map_spells(spell_list, spells_mapping):
    """Map spell IDs to names."""
    if isinstance(spell_list, str):
        spell_list = ast.literal_eval(spell_list)
    return [spells_mapping.get(spell_id, f"UnknownSpell{spell_id}") for spell_id in spell_list]

def extract_keystone(runes):
    """Extract only the first rune (keystone) from the list."""
    if isinstance(runes, str):
        runes = ast.literal_eval(runes)
    return runes[0] if runes else "UnknownKeystone"

def main():
    print("Loading raw database...")
    df = load_data()
    
    # Normalize lanes
    df["lane"] = df["lane"].replace({"UTILITY": "SUPPORT"})
    df["lane"] = df["lane"].str.upper()

    # Normalize champion names
    df["champion_1"] = df["champion_1"].str.strip().str.title()
    df["champion_2"] = df["champion_2"].str.strip().str.title()

    print("Loading champion tags...")
    champion_tags = load_champion_tags()

    print("Applying champion roles to names...")
    df["champion_1"] = df.apply(lambda row: format_champion_with_roles(row["champion_1"], champion_tags.get(row["champion_1"], []), row["lane"]), axis=1)
    df["champion_2"] = df.apply(lambda row: format_champion_with_roles(row["champion_2"], champion_tags.get(row["champion_2"], []), row["lane"]), axis=1)

    print("Loading rune and spell mappings...")
    runes_mapping, spells_mapping = load_runes_and_spells()

    print("Mapping runes and summoner spells...")
    df["runes_1"] = df["runes_1"].apply(lambda x: map_runes(x, runes_mapping))
    df["runes_2"] = df["runes_2"].apply(lambda x: map_runes(x, runes_mapping))
    df["summoner_spells_1"] = df["summoner_spells_1"].apply(lambda x: map_spells(x, spells_mapping))
    df["summoner_spells_2"] = df["summoner_spells_2"].apply(lambda x: map_spells(x, spells_mapping))

    print("Extracting keystones...")
    df["keystone_1"] = df["runes_1"].apply(extract_keystone)
    df["keystone_2"] = df["runes_2"].apply(extract_keystone)

    print("Processing items...")
    print("Loading item mapping from file...")
    with open("patch_diffs/item_mapping.json", "r") as f:
        item_mapping = json.load(f)
    item_mapping = {int(k): v for k, v in item_mapping.items()}

    print("Loading item recipe mapping from file...")
    with open(f"patch_diffs/item_new_{CURRENT_PATCH}.json", "r") as f:
        full_item_data = json.load(f)
        full_item_data = full_item_data.get("data", {})

    # Build a clean recipe_mapping: {item_id: [component_id, ...]}
    recipe_mapping = {}
    for item_id, item_data in full_item_data.items():
        if "from" in item_data:
            recipe_mapping[int(item_id)] = [int(comp_id) for comp_id in item_data["from"]]
    
    early_mid_late_1 = df.apply(lambda row: flatten_items_by_phase(row["items_1"], item_mapping, recipe_mapping, full_item_data, row["match_id"]), axis=1)
    early_mid_late_2 = df.apply(lambda row: flatten_items_by_phase(row["items_2"], item_mapping, recipe_mapping, full_item_data, row["match_id"]), axis=1)

    df["items_1_early"], df["items_1_mid"], df["items_1_late"], df["items_1_end"] = zip(*early_mid_late_1)
    df["items_2_early"], df["items_2_mid"], df["items_2_late"], df["items_2_end"] = zip(*early_mid_late_2)

    # Select only useful columns for LLM fine-tuning
    columns_to_flip = [
    "champion_1", "champion_2", "lane",
    "ally_champions_1", "enemy_champions_1",
    "ally_champions_2", "enemy_champions_2",
    "items_1_early", "items_1_mid", "items_1_late", "items_1_end",
    "items_2_early", "items_2_mid", "items_2_late", "items_2_end",
    "keystone_1", "keystone_2",
    "runes_1", "runes_2",
    "summoner_spells_1", "summoner_spells_2"
    ]

    llm_df = df[columns_to_flip]

    # Create flipped dataset
    flipped_df = llm_df.rename(columns={
        "champion_1": "champion_2",
        "champion_2": "champion_1",
        "ally_champions_1": "ally_champions_2",
        "enemy_champions_1": "enemy_champions_2",
        "ally_champions_2": "ally_champions_1",
        "enemy_champions_2": "enemy_champions_1",
        "items_1_early": "items_2_early",
        "items_1_mid": "items_2_mid",
        "items_1_late": "items_2_late",
        "items_1_end": "items_2_end",
        "items_2_early": "items_1_early",
        "items_2_mid": "items_1_mid",
        "items_2_late": "items_1_late",
        "items_2_end": "items_1_end",
        "keystone_1": "keystone_2",
        "keystone_2": "keystone_1",
        "runes_1": "runes_2",
        "runes_2": "runes_1",
        "summoner_spells_1": "summoner_spells_2",
        "summoner_spells_2": "summoner_spells_1",
    })
    
    columns_to_keep = [
    "champion_1", "champion_2", "lane",
    "ally_champions_1", "enemy_champions_1",
    "ally_champions_2", "enemy_champions_2",
    "items_1_early", "items_1_mid", "items_1_late", "items_1_end",
    "keystone_1", "keystone_2",
    "runes_1", "runes_2",
    "summoner_spells_1", "summoner_spells_2"
    ]

    llm_df = pd.concat([llm_df, flipped_df], ignore_index=True)[columns_to_keep]

    print("Saving processed dataset...")
    llm_df.to_csv(OUTPUT_PATH, index=False, sep=";", quoting=csv.QUOTE_ALL)
    print(f"LLM-ready dataset saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()