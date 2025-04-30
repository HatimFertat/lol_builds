import evaluate

bleu = evaluate.load("bleu")
rouge = evaluate.load("rouge")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = logits.argmax(dim=-1)

    # Decode
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    # Exact Match
    exact_matches = [pred.strip() == label.strip() for pred, label in zip(decoded_preds, decoded_labels)]
    em_score = sum(exact_matches) / len(exact_matches)

    # BLEU and ROUGE
    bleu_result = bleu.compute(predictions=decoded_preds, references=[[l] for l in decoded_labels])
    rouge_result = rouge.compute(predictions=decoded_preds, references=decoded_labels)

    return {
        "exact_match": em_score,
        "bleu": bleu_result["bleu"],
        "rougeL": rouge_result["rougeL"],
    }
