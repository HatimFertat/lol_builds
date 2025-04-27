from unsloth import FastLanguageModel, is_bfloat16_supported
from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling, DataCollatorForSeq2Seq
from datasets import load_dataset
from trl import SFTTrainer
from peft import LoraConfig
import torch
from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
SEED=1515

# ====================
# CONFIGURATION
# ====================
MODEL_NAME = "unsloth/Llama-3.2-3B-bnb-4bit"
TRAIN_FILE = "data/train.jsonl"
VAL_FILE = "data/val.jsonl"
OUTPUT_DIR = "data/llama3b-qlora"

BATCH_SIZE = 48
GRADIENT_ACCUMULATION_STEPS = 1
EPOCHS = 1
MAX_STEPS = 10000
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 0.01
MAX_SEQ_LENGTH = 512
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# ====================
# LOAD MODEL
# ====================
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=torch.bfloat16,
    load_in_4bit=True,
    token=HF_TOKEN,
)

# ====================
# PREPARE LoRA
# ====================
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    random_state=SEED,
    use_rslora= False,
    loftq_config=None,
    use_gradient_checkpointing='unsloth'
)

# ====================
# LOAD DATASET
# ====================
train_dataset = load_dataset("json", data_files=TRAIN_FILE, split="train")
val_dataset = load_dataset("json", data_files=VAL_FILE, split="train")

def tokenize_function(examples):
    full_texts = [p + c for p, c in zip(examples["prompt"], examples["completion"])]
    # full_texts = [f"{p}\n\n### Response:\n{c}" for p, c in zip(examples["prompt"], examples["completion"])]
    tokenized = tokenizer(
        full_texts,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding=False,
        return_tensors=None,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


train_dataset = train_dataset.map(tokenize_function, batched=True, remove_columns=train_dataset.column_names)
val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

lengths = []

for example in train_dataset:
    lengths.append(len(example['input_ids']))

import numpy as np
print("\n=== DEBUG: Sequence Length Stats ===")
print(f"Min Length: {np.min(lengths)}")
print(f"Max Length: {np.max(lengths)}")
print(f"Mean Length: {np.mean(lengths):.2f}")
print(f"95th Percentile Length: {np.percentile(lengths, 95)}")
print(f"99th Percentile Length: {np.percentile(lengths, 99)}")
print(f"99.9th Percentile Length: {np.percentile(lengths, 99.9)}")
print("=====================================\n")


# ====================
# DATA COLLATOR
# ====================
collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    return_tensors="pt",
)

# ====================
# TRAINING
# ====================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY,
    bf16= is_bfloat16_supported(),
    fp16= not is_bfloat16_supported(),
    save_total_limit=2,
    save_strategy="epoch",
    eval_strategy="epoch",
    logging_steps=5,
    optim="adamw_8bit",
    report_to="none",
    seed=SEED
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=collator,
)

trainer.train()

# Save final model
trainer.save_model(OUTPUT_DIR)
print("\n✅ Fine-tuning complete! Model saved to:", OUTPUT_DIR)
