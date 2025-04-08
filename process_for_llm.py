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

def flatten_items_by_phase(item_list, item_mapping):
    """Convert a list of item events into three strings: early, mid, late, handling buys and sells properly."""
    if isinstance(item_list, str):
        item_list = ast.literal_eval(item_list)

    # Sort events by timestamp
    item_list.sort(key=lambda x: x['timestamp'])

    phases = {"early": [], "mid": [], "late": []}

    # IDs for consumable potions and wards to exclude
    excluded_items = {2003, 2031, 2033, 2055, 2056, 3364, 3340, 2010}

    inventory_stack = []

    for event in item_list:
        item_id = event.get('itemId')
        action_raw = event.get('action', '')
        phase = event.get('phase', '')

        if action_raw == "ITEM_PURCHASED":
            inventory_stack.append(("Buy", item_id, phase))
        elif action_raw == "ITEM_SOLD":
            inventory_stack.append(("Sell", item_id, phase))
        elif action_raw == "ITEM_UNDO" and inventory_stack:
            inventory_stack.pop()

    for action_type, item_id, phase in inventory_stack:
        if item_id in excluded_items:
            continue

        item_info = item_mapping.get(item_id)
        item_name = item_info['name'] if item_info else f"UnknownItem{item_id}"

        description = f"{action_type} {item_name}"

        if phase in phases:
            phases[phase].append(description)

    early = " -> ".join(phases["early"])
    mid = " -> ".join(phases["mid"])
    late = " -> ".join(phases["late"])

    return early, mid, late

def main():
    print("Loading raw database...")
    df = load_data()

    # Normalize lanes
    df["lane"] = df["lane"].replace({"UTILITY": "SUPPORT"})
    df["lane"] = df["lane"].str.upper()

    # Normalize champion names
    df["champion_1"] = df["champion_1"].str.strip().str.title()
    df["champion_2"] = df["champion_2"].str.strip().str.title()

    print("Loading item mapping from file...")
    with open("patch_diffs/item_mapping.json", "r") as f:
        item_mapping = json.load(f)
    item_mapping = {int(k): v for k, v in item_mapping.items()}

    print("Processing items...")
    early_mid_late_1 = df["items_1"].apply(lambda x: flatten_items_by_phase(x, item_mapping))
    early_mid_late_2 = df["items_2"].apply(lambda x: flatten_items_by_phase(x, item_mapping))

    df["items_1_early"], df["items_1_mid"], df["items_1_late"] = zip(*early_mid_late_1)
    df["items_2_early"], df["items_2_mid"], df["items_2_late"] = zip(*early_mid_late_2)

    # Select only useful columns for LLM fine-tuning
    columns_to_flip = [
    "champion_1", "champion_2", "lane",
    "ally_champions_1", "enemy_champions_1",
    "ally_champions_2", "enemy_champions_2",
    "items_1_early", "items_1_mid", "items_1_late",
    "items_2_early", "items_2_mid", "items_2_late"
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
    })
    
    columns_to_keep = [
    "champion_1", "champion_2", "lane",
    "ally_champions_1", "enemy_champions_1",
    "ally_champions_2", "enemy_champions_2",
    "items_1_early", "items_1_mid", "items_1_late",
    ]

    llm_df = pd.concat([llm_df, flipped_df], ignore_index=True)[columns_to_keep]

    print("Saving processed dataset...")
    llm_df.to_csv(OUTPUT_PATH, index=False, sep=";")
    print(f"LLM-ready dataset saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()