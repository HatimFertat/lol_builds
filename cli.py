#!/usr/bin/env python3

import argparse
import logging
from config import CURRENT_PATCH_START, REGIONS
from pipeline import process_region, RateLimiter
from db import init_db
import threading
from tqdm import tqdm
import os
from datetime import datetime
os.makedirs('logs', exist_ok=True)
log_filename = datetime.now().strftime('logs/cli_%Y%m%d_%H%M%S.log')

class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            pass

logger = logging.getLogger()  # Changed to use the root logger
logger.setLevel(logging.INFO)

handler = TqdmLoggingHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

routing_limiters = {}
for routing in set(region_info['routing'] for region_info in REGIONS.values()):
    routing_limiters[routing] = {
        "short": RateLimiter(20, 1),
        "long": RateLimiter(100, 120)
    }

def main():
    parser = argparse.ArgumentParser(description="Process League of Legends match data.")
    parser.add_argument('--regions', nargs='*', default=list(REGIONS.keys()), help='List of regions to process')
    parser.add_argument('--patch', type=int, default=CURRENT_PATCH_START, help='Patch start timestamp (Unix time)')
    args = parser.parse_args()

    threads = []
    for region in args.regions:
        logger.info(f"Processing region: {region}")
        t = threading.Thread(target=process_region, args=(region, init_db(), routing_limiters), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    
    tqdm._instances.clear()

if __name__ == "__main__":
    main()