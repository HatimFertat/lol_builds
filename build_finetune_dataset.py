import pandas as pd
import json
from pathlib import Path
import ast
import random

def format_prompt(champion_1, champion_2, lane, allies, enemies, summoner_spells_1, summoner_spells_2, runes_1, keystone_2):
    templates = [
        f"You are playing {champion_1} on the {lane.upper()} lane against {champion_2}. Your team consists of {', '.join(allies)}, while the enemy team includes {', '.join(enemies)}. You have the summoner spells {', '.join(summoner_spells_1)} and the runes {', '.join(runes_1)}. Your opponent uses {', '.join(summoner_spells_2)} and the keystone rune {keystone_2}. What items should you build during the early, mid, and late game?",
        f"Matchup: {champion_1} vs {champion_2} ({lane.upper()} lane). Allies: {', '.join(allies)}. Enemies: {', '.join(enemies)}. You are equipped with {', '.join(summoner_spells_1)} and runes {', '.join(runes_1)}. Your opponent has {', '.join(summoner_spells_2)} and keystone {keystone_2}. Suggest a build for early, mid, and late game.",
        f"As {champion_1} in the {lane.upper()} lane facing {champion_2}, with teammates {', '.join(allies)} against {', '.join(enemies)}, and summoner spells {', '.join(summoner_spells_1)} and runes {', '.join(runes_1)}, while your enemy uses {', '.join(summoner_spells_2)} and keystone {keystone_2}, recommend your item build for all game phases.",
        f"In a {lane.upper()} matchup between {champion_1} and {champion_2}, with allies {', '.join(allies)} and enemies {', '.join(enemies)}, and your setup being {', '.join(summoner_spells_1)} and {', '.join(runes_1)}, versus their {', '.join(summoner_spells_2)} and keystone {keystone_2}, what should you build during early, mid, and late stages?"
    ]
    return random.choice(templates)

def format_completion(early_items, mid_items, late_items):
    def format_items(items):
        if isinstance(items, list):
            return " -> ".join(items) if items else "No items."
        elif isinstance(items, str):
            return items if items.strip() else "No items."
        else:
            return "No items."
    return (
        f"**Early Game:** {format_items(early_items)}\n"
        f"**Mid Game:** {format_items(mid_items)}\n"
        f"**Late Game:** {format_items(late_items)}"
    )

def main():
    input_csv = "data/llm_ready_dataset.csv"
    output_jsonl = "data/build_finetune_dataset.jsonl"
    Path("output").mkdir(parents=True, exist_ok=True)

    # Load patch summaries
    with open("output/champion_patch_important_summary.json", "r") as f:
        champion_patch_summary = json.load(f)
    with open("output/item_patch_important_summary.json", "r") as f:
        item_patch_summary = json.load(f)

    # Prepare champion patch notes lookup
    champion_patch_lookup = {champ.strip().title(): changes for champ, changes in champion_patch_summary.items()}
    item_patch_notes = []
    for item, changes in item_patch_summary.items():
        for change in changes:
            item_patch_notes.append(f"- {change}")
    item_patch_notes_text = "**Item Patch Notes:**\n" + "\n".join(item_patch_notes) + "\n\n"

    df = pd.read_csv(input_csv, sep=';')
    df.fillna('', inplace=True)
    df["ally_champions_1"] = df["ally_champions_1"].apply(ast.literal_eval)
    df["enemy_champions_1"] = df["enemy_champions_1"].apply(ast.literal_eval)
    df["runes_1"] = df["runes_1"].apply(ast.literal_eval)
    df["runes_2"] = df["runes_2"].apply(ast.literal_eval)
    df["summoner_spells_1"] = df["summoner_spells_1"].apply(ast.literal_eval)
    df["summoner_spells_2"] = df["summoner_spells_2"].apply(ast.literal_eval)
    
    with open(output_jsonl, "w") as f_out:
        for _, row in df.iterrows():
            # Collect all champions in this match
            champions_in_game = set(row["ally_champions_1"] + row["enemy_champions_1"] + [row["champion_1"], row["champion_2"]])

            # Filter champion patch notes to only relevant ones
            champ_patch_notes = []
            for champ in champions_in_game:
                simple_name = champ.split("(")[0].strip()  # Remove (roles) from champion name
                changes = champion_patch_lookup.get(simple_name)
                if changes:
                    for change in changes:
                        champ_patch_notes.append(f"- {change}")
            champ_patch_notes_text = "**Champion Patch Notes:**\n" + "\n".join(champ_patch_notes) + "\n\n"

            prompt = champ_patch_notes_text + item_patch_notes_text + format_prompt(
                row["champion_1"],
                row["champion_2"],
                row["lane"],
                row["ally_champions_1"],
                row["enemy_champions_1"],
                row["summoner_spells_1"],
                row["summoner_spells_2"],
                row["runes_1"],
                row["keystone_2"]
            )
            completion = format_completion(
                row["items_1_early"],
                row["items_1_mid"],
                row["items_1_late"]
            )
            record = {"prompt": prompt, "completion": completion}
            json.dump(record, f_out)
            f_out.write("\n")

if __name__ == "__main__":
    main()
