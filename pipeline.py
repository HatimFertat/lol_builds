# pipeline.py

import time
import logging
import argparse
import threading
import queue
from tqdm import tqdm
from threading import Semaphore, Timer
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CURRENT_PATCH_START, REGIONS
from riot_api import (
    fetch_league_players,
    fetch_match_ids_by_puuid,
    fetch_match_details,
    fetch_match_timeline
)
from data_parser import parse_match_data
from db import init_db, insert_match_record

logger = logging.getLogger()

def match_exists(conn, match_id):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM match_records WHERE match_id = ?", (match_id,))
    return cursor.fetchone() is not None

class RateLimiter:
    def __init__(self, calls_per_period, period_seconds):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.call_times = []

    def acquire(self):
        import time
        now = time.time()
        # Remove timestamps older than the current period window
        self.call_times = [t for t in self.call_times if now - t < self.period_seconds]
        if len(self.call_times) >= self.calls_per_period:
            sleep_time = self.period_seconds - (now - self.call_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.call_times.append(time.time())

def process_match(region, match_id, short_term_limiter, long_term_limiter):
    conn = init_db()
    if match_exists(conn, match_id):
        logger.info(f"Skipping already processed match {match_id}")
        conn.close()
        return
    try:
        short_term_limiter.acquire()
        long_term_limiter.acquire()
        match_detail = fetch_match_details(region, match_id)

        short_term_limiter.acquire()
        long_term_limiter.acquire()
        timeline = fetch_match_timeline(region, match_id)
    except Exception as e:
        logger.error(f"Error fetching match details/timeline for match {match_id}: {e}")
        conn.close()
        return

    if match_detail and timeline:
        records = parse_match_data(match_detail, timeline)
        for record in records:
            record["patch_start"] = CURRENT_PATCH_START
            record["region"] = region
            record["match_id"] = match_id
            insert_match_record(conn, record)
    
    conn.close()

def process_region(region, conn, routing_limiters):
    from config import REGIONS  # Ensure REGIONS is available

    routing = REGIONS[region]['routing']
    short_term_limiter = routing_limiters[routing]['short']
    long_term_limiter = routing_limiters[routing]['long']

    tiers = ["CHALLENGER"]
    puuids = []
    for tier in tiers:
        league_data = fetch_league_players(region, tier=tier)
        if league_data and 'entries' in league_data:
            puuids.extend(player['puuid'] for player in league_data['entries'] if 'puuid' in player)
    if not puuids:
        logger.info(f"No league data for region: {region}")
        return
    logger.info(f"Region {region}: Fetched {len(puuids)} PUUIDs.")
    
    MATCHES_PER_PUUID = 5
    total_match_requests = len(puuids) * MATCHES_PER_PUUID
    logger.info(f"Region {region}: Planning to request {total_match_requests} match details ({MATCHES_PER_PUUID} per player).")

    all_match_ids = []

    for puuid in tqdm(puuids, desc=f"Fetching matches for players in {region}"):
        try:
            short_term_limiter.acquire()
            long_term_limiter.acquire()
            match_ids = fetch_match_ids_by_puuid(region, puuid, CURRENT_PATCH_START, count=MATCHES_PER_PUUID)
            logger.info(f"PUUID {puuid}: Retrieved {len(match_ids)} match IDs.")
            all_match_ids.extend(match_ids)
        except Exception as e:
            logger.error(f"Error fetching match IDs for puuid {puuid}: {e}")
            continue

    unique_match_ids = list(set(all_match_ids))
    logger.info(f"Region {region}: {len(unique_match_ids)} unique matches to process.")

    for match_id in tqdm(unique_match_ids, desc=f"Processing matches in {region}"):
        process_match(region, match_id, short_term_limiter, long_term_limiter)
