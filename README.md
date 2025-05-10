# League of Legends LLM Build Recommender

This project builds a League of Legends (LoL) item build recommender using large language models (LLMs). It automates the process of collecting, processing, and transforming match data, then fine-tunes an LLM (such as Llama-3) to generate item build recommendations for specific matchups, lanes, and champion setups.

## Features
- **Automated Data Pipeline**: Fetches and parses match data from the Riot API, including champions, items, runes, and summoner spells.
- **Patch Awareness**: Integrates champion and item patch notes into prompts for the LLM, making recommendations patch-aware.
- **Dataset Builder**: Converts processed match data into prompt-completion pairs for supervised fine-tuning.
- **Fine-tuning Scripts**: Uses Unsloth and HuggingFace Trainer for efficient LLM fine-tuning with LoRA.
- **Evaluation and Inference**: Provides scripts and notebooks for model evaluation and prediction.

## Project Structure
- `src/core/pipeline/`: Data extraction and parsing (e.g., `riot_api.py`, `data_parser.py`, `patch_diff.py`).
- `src/core/finetune/`: Dataset processing, splitting, fine-tuning, and evaluation scripts.
- `patch_diffs/`: Patch summaries and mappings for champions, items, runes, and spells.
- `data/`: Raw and processed datasets, patch diffs, and model outputs.
- `unsloth_compiled_cache/`: Compiled trainer classes for various RLHF algorithms.

## Setup & Requirements
- Python 3.8+
- PyTorch, Transformers, Datasets, Unsloth, TRL, dotenv, tqdm, pandas, etc.
- Access to a Nvidia GPU for Unsloth.
- Riot API key for data collection.

Install dependencies:
```bash
python -m venv .venv
source activate .venv/bin/activate
pip install .
```

## Usage
1. **Data Processing**: Run the pipeline to fetch and process match data from the Riot API.
2. **Dataset Preparation**: Use scripts in `src/core/finetune/` to process, build, and split the dataset.
3. **Fine-tuning**: Run the fine-tuning script to train the LLM on the prepared dataset.
4. **Evaluation/Inference**: Use evaluation scripts or notebooks to test the model’s recommendations.

Example workflow:
```bash
#Acquire data
pyton cli.py

# Process and prepare data
python src/core/finetune/process_for_llm.py
python src/core/finetune/build_finetune_dataset.py
python src/core/finetune/split_train_test.py

# Fine-tune the model
python src/core/finetune/finetune.py
```

## Dataset Format
Each training example is a JSON object with a `prompt` (including matchup, patch notes, etc.) and a `completion` (recommended item build for early, mid, late game, and final inventory).

## Example Prompt/Completion
```
📝 PROMPT:
**Champion Patch Notes:**
- Darius spell 2 updated.
- Darius armor decreased from 39 to 37.
- Nasus spell 3 label changed across ranks.

In a JUNGLE matchup between Ekko (assassin/mage) and Rammus (tank), with allies Darius, Nasus, Kaisa, Leona and enemies Rammus, Shen, Smolder, Ziggs, Rell, and your setup being Smite, Flash and Dark Harvest, Sudden Impact, Grisly Mementos, Treasure Hunter, Magical Footwear, Jack Of All Trades, versus their Smite, Ghost and keystone Aftershock, what should you build during early, mid, and late stages?

✅ GROUND TRUTH COMPLETION:
**Early Game:**
Buy Gustwalker Hatchling
Inventory (1): Gustwalker Hatchling
...
**Mid Game:**
Build Nashor's Tooth (fusing Recurve Bow + Blasting Wand + Fiendish Codex)
Inventory (2): Gustwalker Hatchling, Nashor's Tooth
...
**Late Game:**
No items.
**Final inventory:**
Gustwalker Hatchling, Nashor's Tooth, Lich Bane, Sorcerer's Shoes, Blighting Jewel, Blasting Wand
```
