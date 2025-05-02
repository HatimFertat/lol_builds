import ast
from process_for_llm import flatten_items_by_phase
import json

print("Loading item recipe mapping from file...")
with open("patch_diffs/item_new_15.7.1.json", "r") as f:
    full_item_data = json.load(f)
    full_item_data = full_item_data.get("data", {})

with open("patch_diffs/item_mapping.json", "r") as f:
        item_mapping = json.load(f)
item_mapping = {int(k): v for k, v in item_mapping.items()}

# Build a clean recipe_mapping: {item_id: [component_id, ...]}
recipe_mapping = {}
for item_id, item_data in full_item_data.items():
    if "from" in item_data:
        recipe_mapping[int(item_id)] = [int(comp_id) for comp_id in item_data["from"]]

# print(recipe_mapping)
# Assume flatten_items_by_phase is already imported from your code

def printing_function(item_list, item_mapping=item_mapping, recipe_mapping=recipe_mapping, full_item_data=full_item_data):
    early, mid, late, final_inventory = flatten_items_by_phase(item_list, item_mapping, recipe_mapping, full_item_data)
    print("==== EARLY GAME ====")
    print(early)
    print("\n==== MID GAME ====")
    print(mid)
    print("\n==== LATE GAME ====")
    print(late)
    print("\n==== FINAL INVENTORY ====")
    print(final_inventory)

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

item_list_3 = [{'itemId': 1101, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 99520},
{'itemId': 2003, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 100054},
{'itemId': 3051, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 342746},
{'itemId': 1028, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 342812},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 342846},
{'itemId': 3057, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 458414},
{'itemId': 3078, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 570823},
{'itemId': 1001, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 571691},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 573895},
{'itemId': 1042, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 575164},
{'itemId': 3006, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 811138},
{'itemId': 3134, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 811806},
{'itemId': 1037, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 967665},
{'itemId': 1018, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 967732},
{'itemId': 3364, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 969068},
{'itemId': 6676, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1076120},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1122183},
{'itemId': 3036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1386406},
{'itemId': 2055, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1420677},
{'itemId': 1018, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1500048},
{'itemId': 1042, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1500694},
{'itemId': 3094, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1698184},
{'itemId': 1018, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1699569}]

item_list_4 = [{'itemId': 1102, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 13612},
{'itemId': 3134, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 248487},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 248821},
{'itemId': 3364, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 250424},
{'itemId': 6690, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 386436},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 386636},
{'itemId': 3142, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 523848},
{'itemId': 3134, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 525418},
{'itemId': 3158, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 592205},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'early', 'timestamp': 593643},
{'itemId': 3009, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 595113},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 703548},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 703648},
{'itemId': 3133, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 787113},
{'itemId': 6697, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1001965},
{'itemId': 3134, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1007716},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1007883},
{'itemId': 2021, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1096676},
{'itemId': 3814, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1225809},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1226577},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1226711},
{'itemId': 3035, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1325813},
{'itemId': 6694, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1606256},
{'itemId': 1036, 'action': 'ITEM_PURCHASED', 'phase': 'late', 'timestamp': 1606862}]

item_list_5=[{'itemId': 3865, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 7164},
{'itemId': 2003, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 7564},
{'itemId': 2003, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 7731},
{'itemId': 3340, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 9368},
{'itemId': 1001, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 210315},
{'itemId': 2031, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 210883},
{'itemId': 3010, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 417940},
{'itemId': 1028, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 419577},
{'itemId': 1029, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 420232},
{'itemId': 3364, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 422303},
{'itemId': 3067, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 581654},
{'itemId': 1033, 'action': 'ITEM_PURCHASED', 'phase': 'early', 'timestamp': 582422},
{'itemId': 3050, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 728046},
{'itemId': 3869, 'action': 'ITEM_SOLD', 'phase': 'mid', 'timestamp': 968199},
{'itemId': 3050, 'action': 'ITEM_SOLD', 'phase': 'mid', 'timestamp': 968499},
{'itemId': 3013, 'action': 'ITEM_SOLD', 'phase': 'mid', 'timestamp': 968800},
{'itemId': 2031, 'action': 'ITEM_SOLD', 'phase': 'mid', 'timestamp': 969067},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 970035},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 970202},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 970603},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 970737},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 970904},
{'itemId': 1027, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 971037},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 994825},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 994992},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995159},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995326},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995493},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995627},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995761},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 995862},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 996129},
{'itemId': None, 'action': 'ITEM_UNDO', 'phase': 'mid', 'timestamp': 996296},
{'itemId': 3067, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 999037},
{'itemId': 2055, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 999805},
{'itemId': 2031, 'action': 'ITEM_SOLD', 'phase': 'mid', 'timestamp': 1250570},
{'itemId': 1031, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1252140},
{'itemId': 2055, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1253017},
{'itemId': 3109, 'action': 'ITEM_PURCHASED', 'phase': 'mid', 'timestamp': 1378866}]

item_list_6 = [{'itemId': 3865, 'timestamp': 6726, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2003, 'timestamp': 6726, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2003, 'timestamp': 6726, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 3340, 'timestamp': 7461, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2003, 'timestamp': 208997, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 2010, 'timestamp': 209165, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 1001, 'timestamp': 229938, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 231140, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 256900, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 2003, 'timestamp': 359890, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 2010, 'timestamp': 360090, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 1033, 'timestamp': 378232, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 379167, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 3340, 'timestamp': 379401, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 3364, 'timestamp': 379401, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 407241, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 1001, 'timestamp': 439470, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 1033, 'timestamp': 439470, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 3111, 'timestamp': 439470, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 3865, 'timestamp': 450096, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 2010, 'timestamp': 506338, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 3067, 'timestamp': 615210, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1029, 'timestamp': 697919, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1033, 'timestamp': 779932, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 3866, 'timestamp': 997578, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3867, 'timestamp': 999015, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3067, 'timestamp': 1029056, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 1029, 'timestamp': 1029056, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 1033, 'timestamp': 1029056, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3190, 'timestamp': 1029056, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1028, 'timestamp': 1030759, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1028, 'timestamp': 1131900, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3067, 'timestamp': 1131900, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1132803, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1133070, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1163933, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 1004, 'timestamp': 1216347, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1004, 'timestamp': 1228917, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3114, 'timestamp': 1228917, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1380669, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3067, 'timestamp': 1519673, 'phase': 'late', 'action': 'ITEM_DESTROYED'}, {'itemId': 3114, 'timestamp': 1519673, 'phase': 'late', 'action': 'ITEM_DESTROYED'}, {'itemId': 3107, 'timestamp': 1519673, 'phase': 'late', 'action': 'ITEM_PURCHASED'}, {'itemId': 3067, 'timestamp': 1520575, 'phase': 'late', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1521343, 'phase': 'late', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1578487, 'phase': 'late', 'action': 'ITEM_DESTROYED'}]

printing_function(item_list_6)

item_list_7 = [{'itemId': 1101, 'timestamp': 24761, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 2508, 'timestamp': 244734, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 3340, 'timestamp': 245669, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 3364, 'timestamp': 245669, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 1052, 'timestamp': 308882, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 1001, 'timestamp': 384544, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 1027, 'timestamp': 385613, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 1052, 'timestamp': 506939, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 1027, 'timestamp': 506939, 'phase': 'early', 'action': 'ITEM_DESTROYED'}, {'itemId': 3802, 'timestamp': 506939, 'phase': 'early', 'action': 'ITEM_PURCHASED'}, {'itemId': 3802, 'timestamp': 716427, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 2508, 'timestamp': 716427, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 2503, 'timestamp': 716427, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2508, 'timestamp': 718364, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1001, 'timestamp': 893823, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3020, 'timestamp': 893823, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1028, 'timestamp': 919844, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1101, 'timestamp': 1049441, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 1028, 'timestamp': 1087110, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3147, 'timestamp': 1087110, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1088546, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1161453, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 3147, 'timestamp': 1209868, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 2508, 'timestamp': 1209868, 'phase': 'mid', 'action': 'ITEM_DESTROYED'}, {'itemId': 6653, 'timestamp': 1209868, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1232557, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1052, 'timestamp': 1321700, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 1028, 'timestamp': 1472291, 'phase': 'mid', 'action': 'ITEM_PURCHASED'}, {'itemId': 2055, 'timestamp': 1569086, 'phase': 'late', 'action': 'ITEM_DESTROYED'}, {'itemId': 1026, 'timestamp': 1654997, 'phase': 'late', 'action': 'ITEM_PURCHASED'}]

# printing_function(item_list_7)