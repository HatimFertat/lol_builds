#!/bin/bash

echo "Starting task with data fetch at $(date)" 
python cli.py

echo "Starting data processing at $(date)" 
python process_for_llm.py
python build_finetune_dataset.py
python split_train_test.py

echo "Starting finetuning task with at $(date)" 
python finetune.py