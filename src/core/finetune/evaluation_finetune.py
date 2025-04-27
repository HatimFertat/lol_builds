from unsloth import FastLanguageModel
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import load_dataset
import torch
import os

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="data/llama3b-qlora",  # your OUTPUT_DIR
    max_seq_length=512,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

# Load dataset
val_dataset = load_dataset("json", data_files="data/val.jsonl", split="train")

def tokenize_function(examples):
    full_texts = [p + c for p, c in zip(examples["prompt"], examples["completion"])]
    tokenized = tokenizer(
        full_texts,
        truncation=True,
        max_length=512,
        padding=False,
        return_tensors=None,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

# Prepare collator
collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    return_tensors="pt",
)

# Setup Trainer for evaluation
training_args = TrainingArguments(
    output_dir="eval_output",
    per_device_eval_batch_size=64,
    bf16=torch.cuda.is_bf16_supported(),
    fp16=not torch.cuda.is_bf16_supported(),
    report_to="none",
)

trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    data_collator=collator,
    eval_dataset=val_dataset,
)

# Run evaluation
metrics = trainer.evaluate()
print("\n=== Evaluation Metrics ===")
print(metrics)
print("===========================\n")
