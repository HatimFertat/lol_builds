import random
from pathlib import Path

# ====================
# CONFIGURATION
# ====================
INPUT_JSONL = "data/build_finetune_dataset.jsonl"
TRAIN_JSONL = "data/train.jsonl"
VAL_JSONL = "data/val.jsonl"
TRAIN_SPLIT = 0.9  # 90% train, 10% validation

# ====================
# LOAD AND SPLIT
# ====================
lines = Path(INPUT_JSONL).read_text().strip().split("\n")
random.shuffle(lines)

split_idx = int(len(lines) * TRAIN_SPLIT)
train_lines = lines[:split_idx]
val_lines = lines[split_idx:]

# ====================
# SAVE
# ====================
Path(TRAIN_JSONL).write_text("\n".join(train_lines))
Path(VAL_JSONL).write_text("\n".join(val_lines))

print(f"✅ Done. Train samples: {len(train_lines)}, Validation samples: {len(val_lines)}")
