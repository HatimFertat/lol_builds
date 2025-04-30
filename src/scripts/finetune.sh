#!/bin/bash

echo "Starting data processing at $(date)" 
python src/core/finetune/process_for_llm.py
python src/core/finetune/build_finetune_dataset.py
python src/core/finetune/split_train_test.py

echo "Starting finetuning task with at $(date)" 
python src/core/finetune/finetune.py
python src/core/finetune/hfpush.py