from huggingface_hub import login
from unsloth import FastLanguageModel, is_bfloat16_supported
from datasets import load_dataset, DatasetDict, Dataset, DatasetInfo
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer
from transformers import Trainer, TrainingArguments, AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq
from dotenv import load_dotenv
import os
import shutil

push_dataset = True

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
SEED=1515
MODEL_NAME = "unsloth/Llama-3.2-3B-bnb-4bit"
TRAIN_FILE = "data/train.jsonl"
VAL_FILE = "data/val.jsonl"
OUTPUT_DIR = "data/llama3b-qlora"
REPO_ID = "HatimF/LoL_Build-Llama3B"
BATCH_SIZE = 32
GRADIENT_ACCUMULATION_STEPS = 1
EPOCHS = 1
MAX_STEPS = 10000
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 0.01
MAX_SEQ_LENGTH = 512
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

LATEST_CHECKPOINT = os.path.join(OUTPUT_DIR, "checkpoint-2386")

shutil.copy(os.path.join(LATEST_CHECKPOINT, "trainer_state.json"), os.path.join(OUTPUT_DIR, "trainer_state.json"))

# Login to Hugging Face Hub
login(token=HF_TOKEN)

# Load the fine-tuned model and tokenizer
model = AutoModelForCausalLM.from_pretrained(OUTPUT_DIR)
tokenizer = AutoTokenizer.from_pretrained(OUTPUT_DIR)

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


# train_dataset = train_dataset.map(tokenize_function, batched=True, remove_columns=train_dataset.column_names)
# val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

if push_dataset:    
    dataset = DatasetDict({
        "train": train_dataset,
        "validation": val_dataset})

    dataset.push_to_hub("HatimF/lol_build_dataset")



# Load model and tokenizer
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    do_train=False,
    do_eval=False,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY,
    save_total_limit=2,
    save_strategy="epoch",
    eval_strategy="epoch",
    logging_steps=5,
    optim="adamw_8bit",
    report_to="none",
    seed=SEED,
    hub_token=HF_TOKEN,
    hub_model_id=REPO_ID,
    push_to_hub=True
)

collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    return_tensors="pt",
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args
)

import json

with open(os.path.join(OUTPUT_DIR, "trainer_state.json")) as f:
    trainer_state = json.load(f)

train_losses = [entry["loss"] for entry in trainer_state["log_history"] if "loss" in entry]
eval_losses = [entry["eval_loss"] for entry in trainer_state["log_history"] if "eval_loss" in entry]

final_train_loss = train_losses[-1] if train_losses else None
final_eval_loss = eval_losses[-1] if eval_losses else None

print("Final Train Loss:", final_train_loss)

trainer.push_to_hub()
