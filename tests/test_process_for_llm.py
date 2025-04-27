import ast
from src.core.process_for_llm import flatten_items_by_phase
import json

print("Loading item recipe mapping from file...")
with open("patch_diffs/item_new_15.7.1.json", "r") as f:
    full_item_data = json.load(f)
    full_item_data = full_item_data.get("data", {})

# Build a clean recipe_mapping: {item_id: [component_id, ...]}
recipe_mapping = {}
for item_id, item_data in full_item_data.items():
    if "from" in item_data:
        recipe_mapping[int(item_id)] = [int(comp_id) for comp_id in item_data["from"]]

# print(recipe_mapping)
# Assume flatten_items_by_phase is already imported from your code

# Fake simple item_mapping (normally from Riot's API data)
item_mapping = {
    1052: "Amplifying Tome",
    3108: "Fiendish Codex",
    3802: "Lost Chapter",
    3070: "Tear of the Goddess",
    6655: "Luden's Companion",
    1027: "Sapphire Crystal",
    3003: "Archangel's Staff"
}

# Fake timeline of events
# (timestamps in ms, arbitrary but showing build happening around 5000ms)
item_list = [
    {"itemId": 1052, "timestamp": 1000, "phase": "early", "action": "ITEM_PURCHASED"}, # Buy Tome
    {"itemId": 1052, "timestamp": 2500, "phase": "early", "action": "ITEM_DESTROYED"}, # Destroy Tome
    {"itemId": 3108, "timestamp": 3000, "phase": "early", "action": "ITEM_PURCHASED"}, # Buy Codex
    {"itemId": 1052, "timestamp": 3500, "phase": "early", "action": "ITEM_PURCHASED"}, # Buy Tome
    {"itemId": 1052, "timestamp": 6000, "phase": "early", "action": "ITEM_DESTROYED"}, # Destroy Tome
    {"itemId": 3802, "timestamp": 6100, "phase": "early", "action": "ITEM_PURCHASED"}, # Buy Lost Chapter (build)
    {"itemId": 3802, "timestamp": 9000, "phase": "early", "action": "ITEM_SOLD"},       # Sell Lost Chapter
    {"itemId": 6655, "timestamp": 1600000, "phase": "late", "action": "ITEM_PURCHASED"}, # Buy Luden's Tempest
]

# Run through the flattening function
early, mid, late, final_inventory = flatten_items_by_phase(item_list, item_mapping, recipe_mapping)

# Print results
print("==== EARLY GAME ====")
print(early)
print("\n==== MID GAME ====")
print(mid)
print("\n==== LATE GAME ====")
print(late)
print("\n==== FINAL INVENTORY ====")
print(final_inventory)







## Test Case 2: Correct Archangel's Staff build (Tear of the Goddess + Lost Chapter + Fiendish Codex)
# Archangel's Staff (3040) builds from: 3070 (Tear), 3802 (Lost Chapter), 3108 (Codex)
# Timeline: buy Codex, buy Tear, buy Lost Chapter, destroy all 3, buy Archangel's Staff, sell it
item_list_2 = [
    {"itemId": 3108, "timestamp": 1000, "phase": "early", "action": "ITEM_PURCHASED"},   # Buy Fiendish Codex
    {"itemId": 3070, "timestamp": 1500, "phase": "early", "action": "ITEM_PURCHASED"},   # Buy Tear of the Goddess
    {"itemId": 3802, "timestamp": 2000, "phase": "early", "action": "ITEM_PURCHASED"},   # Buy Lost Chapter
    {"itemId": 3108, "timestamp": 2500, "phase": "early", "action": "ITEM_DESTROYED"},   # Destroy Codex
    {"itemId": 3070, "timestamp": 2500, "phase": "early", "action": "ITEM_DESTROYED"},   # Destroy Tear
    {"itemId": 3802, "timestamp": 2500, "phase": "early", "action": "ITEM_DESTROYED"},   # Destroy Lost Chapter
    {"itemId": 3003, "timestamp": 3000, "phase": "early", "action": "ITEM_PURCHASED"},   # Buy Archangel's Staff
    {"itemId": 3003, "timestamp": 4000, "phase": "early", "action": "ITEM_SOLD"},        # Sell Archangel's Staff
]

early2, mid2, late2, final_inventory2 = flatten_items_by_phase(item_list_2, item_mapping, recipe_mapping)

print("\n==== TEST CASE 2: EARLY GAME ====")
print(early2)
print("\n==== TEST CASE 2: MID GAME ====")
print(mid2)
print("\n==== TEST CASE 2: LATE GAME ====")
print(late2)
print("\n==== TEST CASE 2: FINAL INVENTORY ====")
print(final_inventory2)