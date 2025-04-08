import pandas as pd
import json
from pathlib import Path
import ast
import random

def format_prompt(champion_1, champion_2, lane, allies, enemies):
    templates = [
        f"You are playing {champion_1} on the {lane.upper()} lane against {champion_2}. Your team consists of {', '.join(allies)}, while the enemy team includes {', '.join(enemies)}. What items should you build during the early, mid, and late game?",
        f"Matchup: {champion_1} vs {champion_2} ({lane.upper()} lane). Allies: {', '.join(allies)}. Enemies: {', '.join(enemies)}. Suggest a build for early, mid, and late game.",
        f"As {champion_1} in the {lane.upper()} lane facing {champion_2}, with teammates {', '.join(allies)} against {', '.join(enemies)}, recommend your item build for all game phases.",
        f"In a {lane.upper()} matchup between {champion_1} and {champion_2}, with allies {', '.join(allies)} and enemies {', '.join(enemies)}, what should you build during early, mid, and late stages?"
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

    df = pd.read_csv(input_csv, sep=';')
    df.fillna('', inplace=True)
    df["ally_champions_1"] = df["ally_champions_1"].apply(ast.literal_eval)
    df["enemy_champions_1"] = df["enemy_champions_1"].apply(ast.literal_eval)
    
    with open(output_jsonl, "w") as f_out:
        for _, row in df.iterrows():
            prompt = format_prompt(
                row["champion_1"],
                row["champion_2"],
                row["lane"],
                row["ally_champions_1"],
                row["enemy_champions_1"]
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
