import sqlite3
import pandas as pd
import json
import ast

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

def flatten_items_by_phase(item_list, item_mapping, recipe_mapping):
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
    excluded_items = {2003, 2031, 2033, 2055, 2056, 3364, 3340, 2010, 2138, 2139, 2140, 2150, 2151, 2152}

    inventory_stack = []
    current_inventory = []
    recently_destroyed = []

    for event in item_list:
        item_id = event.get('itemId')
        action_raw = event.get('action', '')
        phase = event.get('phase', '')
        timestamp = event.get('timestamp', 0)

        #print(f"Processing event: {action_raw} {item_id} at {timestamp}")

        if action_raw == "ITEM_PURCHASED":
            recipe_components = recipe_mapping.get(item_id, [])
            recipe_components = [comp for comp in recipe_components]

            # Combine current inventory with items destroyed very recently (acts as a short‑lived buffer for fusions).
            inventory_and_recent = current_inventory + [
                comp_id for comp_id, comp_time in recently_destroyed
                if timestamp - comp_time <= 1000
            ]

            # A build is possible when the item has recipe components and at least one of them is available
            # either in the current inventory OR in the short‑lived destroyed buffer.
            has_any_component = any(comp in inventory_and_recent for comp in recipe_components)
            can_build = bool(recipe_components) and has_any_component

            #print(f"Recipe components for {item_id}: {recipe_components}")
            #print(f"Can build {item_id}? {can_build}")
            if recipe_components and can_build:
                # Treat as Build
                # Remove only the components that actually existed in inventory or were recently destroyed.
                for comp_id in recipe_components:
                    if comp_id in current_inventory:
                        current_inventory.remove(comp_id)
                    # Also clean from recently_destroyed if present
                    recently_destroyed = [(id_, t) for id_, t in recently_destroyed if id_ != comp_id]
                inventory_stack.append(("Build", item_id, phase, recipe_components))
                current_inventory.append(item_id)
                #print(f"Action taken: Build {item_id}")
                #print(f"Current inventory after action: {current_inventory}")
                # Log the build event chronologically
                item_name = item_mapping.get(item_id, f"Unknown{item_id}")
                component_names = [
                    item_mapping.get(comp_id, f"Unknown{comp_id}")
                    for comp_id in recipe_components
                    if comp_id not in excluded_items and comp_id != 2022
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
        elif action_raw == "ITEM_DESTROYED":
            recently_destroyed.append((item_id, timestamp))
            if item_id in current_inventory:
                current_inventory.remove(item_id)
            #print(f"Item destroyed: {item_id}, Current inventory: {current_inventory}")
        elif action_raw == "ITEM_UNDO":
            if inventory_stack:
                last_action = inventory_stack.pop()
                if last_action[0] == "Buy":
                    last_item_id = last_action[1]
                    if last_item_id in current_inventory:
                        current_inventory.remove(last_item_id)
                elif last_action[0] == "Sell":
                    last_item_id = last_action[1]
                    current_inventory.append(last_item_id)
                elif last_action[0] == "Build":
                    last_item_id = last_action[1]
                    if last_item_id in current_inventory:
                        current_inventory.remove(last_item_id)
            #print(f"Undo action, New inventory: {current_inventory}")

    early = "\n".join(phases["early"])
    mid = "\n".join(phases["mid"])
    late = "\n".join(phases["late"])

    final_inventory_list = [item_mapping.get(item_id) for item_id in current_inventory if item_id not in excluded_items and item_mapping.get(item_id)]

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
    with open("patch_diffs/item_new_15.7.1.json", "r") as f:
        full_item_data = json.load(f)
        full_item_data = full_item_data.get("data", {})

    # Build a clean recipe_mapping: {item_id: [component_id, ...]}
    recipe_mapping = {}
    for item_id, item_data in full_item_data.items():
        if "from" in item_data:
            recipe_mapping[int(item_id)] = [int(comp_id) for comp_id in item_data["from"]]

    early_mid_late_1 = df["items_1"].apply(lambda x: flatten_items_by_phase(x, item_mapping, recipe_mapping))
    early_mid_late_2 = df["items_2"].apply(lambda x: flatten_items_by_phase(x, item_mapping, recipe_mapping))

    df["items_1_early"], df["items_1_mid"], df["items_1_late"], df["items_1_inventory"] = zip(*early_mid_late_1)
    df["items_2_early"], df["items_2_mid"], df["items_2_late"], df["items_2_inventory"] = zip(*early_mid_late_2)

    # Select only useful columns for LLM fine-tuning
    columns_to_flip = [
    "champion_1", "champion_2", "lane",
    "ally_champions_1", "enemy_champions_1",
    "ally_champions_2", "enemy_champions_2",
    "items_1_early", "items_1_mid", "items_1_late",
    "items_2_early", "items_2_mid", "items_2_late",
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
        "items_2_early": "items_1_early",
        "items_2_mid": "items_1_mid",
        "items_2_late": "items_1_late",
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
    "items_1_early", "items_1_mid", "items_1_late",
    "keystone_1", "keystone_2",
    "runes_1", "runes_2",
    "summoner_spells_1", "summoner_spells_2"
    ]

    llm_df = pd.concat([llm_df, flipped_df], ignore_index=True)[columns_to_keep]

    print("Saving processed dataset...")
    llm_df.to_csv(OUTPUT_PATH, index=False, sep=";")
    print(f"LLM-ready dataset saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()