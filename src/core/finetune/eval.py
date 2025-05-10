from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from evaluate import load
import torch
from tqdm import tqdm  # Import tqdm for progress tracking
from torch.utils.data import DataLoader  # Import DataLoader for batching
from transformers import DataCollatorForSeq2Seq  # Import DataCollatorForSeq2Seq for padding and batching

# Load model and tokenizer
model_path = "data/llama3b-qlora"
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer
import torch
from datasets import load_dataset
from transformers import DataCollatorForSeq2Seq
from torch.utils.data import DataLoader
from tqdm import tqdm
from evaluate import load

# Set left padding for decoder-only models

tokenizer = AutoTokenizer.from_pretrained(model_path)
tokenizer.padding_side = "left"
model = AutoPeftModelForCausalLM.from_pretrained(model_path, device_map="auto").eval()

# Load validation data
val_dataset = load_dataset("json", data_files="data/val.jsonl", split="train")

# Tokenization (batched, with labels)
def tokenize_function(examples):
    full_texts = [p + c for p, c in zip(examples["prompt"], examples["completion"])]
    tokenized = tokenizer(
        full_texts,
        truncation=True,
        max_length=1024,
        padding=False,
        return_tensors=None,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

val_dataset = val_dataset.map(tokenize_function, batched=True, remove_columns=val_dataset.column_names)

# Data collator for padding and batching
collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    return_tensors="pt",
)

batch_size = 22

data_loader = DataLoader(val_dataset, batch_size=batch_size, collate_fn=collator)

bleu = load("bleu")
rouge = load("rouge")

decoded_preds, decoded_labels = [], []
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

for batch in tqdm(data_loader, desc="Evaluating"):
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch.get("attention_mask", None)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)
    with torch.no_grad():
        outputs = model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=100)
    preds = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    # Fix: replace -100 with pad_token_id before decoding labels
    labels = batch["labels"].clone()
    labels[labels == -100] = tokenizer.pad_token_id
    labels = labels.to(device)
    decoded = tokenizer.batch_decode(labels, skip_special_tokens=True)
    decoded_preds.extend([p.strip() for p in preds])
    decoded_labels.extend([l.strip() for l in decoded])

results = {
    "BLEU": bleu.compute(predictions=decoded_preds, references=[[l] for l in decoded_labels])["bleu"],
    "ROUGE-L": rouge.compute(predictions=decoded_preds, references=decoded_labels)["rougeL"],
    "Exact Match": sum(p == l for p, l in zip(decoded_preds, decoded_labels)) / len(decoded_preds)
}

print(results)
