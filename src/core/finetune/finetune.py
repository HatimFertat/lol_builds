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
REPO_ID = "HatimF/LoL_Build-Llama3B"

BATCH_SIZE = 16
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


import evaluate

bleu = evaluate.load("bleu")
rouge = evaluate.load("rouge")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(torch.tensor(logits), dim=-1)

    # Batched decoding to reduce memory footprint
    batch_size = 8
    decoded_preds, decoded_labels = [], []
    for i in range(0, len(predictions), batch_size):
        decoded_preds.extend(tokenizer.batch_decode(predictions[i:i+batch_size], skip_special_tokens=True))
        decoded_labels.extend(tokenizer.batch_decode(labels[i:i+batch_size], skip_special_tokens=True))

    exact_matches = [pred.strip() == label.strip() for pred, label in zip(decoded_preds, decoded_labels)]
    em_score = sum(exact_matches) / len(exact_matches)

    bleu_result = bleu.compute(predictions=decoded_preds, references=[[l] for l in decoded_labels])
    rouge_result = rouge.compute(predictions=decoded_preds, references=decoded_labels)

    return {
        "exact_match": em_score,
        "bleu": bleu_result["bleu"],
        "rougeL": rouge_result["rougeL"],
    }


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
    seed=SEED,
    hub_token=HF_TOKEN,
    hub_model_id=REPO_ID
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=collator,
    compute_metrics=compute_metrics,
)

trainer.train()

# Save final model
trainer.save_model(OUTPUT_DIR)
print("\n✅ Fine-tuning complete! Model saved to:", OUTPUT_DIR)

trainer.evaluate()
trainer.push_to_hub()