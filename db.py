import sqlite3

def init_db(db_path="matches.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_records (
        match_id TEXT,
        patch_start INTEGER,
        region TEXT,
        lane TEXT,
        champion_1 TEXT,
        champion_2 TEXT,
        win_1 BOOLEAN,
        win_2 BOOLEAN,
        kda_1 TEXT,
        kda_2 TEXT,
        gold_1 INTEGER,
        gold_2 INTEGER,
        items_1 TEXT,
        items_2 TEXT,
        damage_dealt_1 INTEGER,
        damage_dealt_2 INTEGER,
        damage_taken_1 INTEGER,
        damage_taken_2 INTEGER,
        damage_to_objectives_1 INTEGER,
        damage_to_objectives_2 INTEGER,
        vision_score_1 REAL,
        vision_score_2 REAL,
        cs_1 REAL,
        cs_2 REAL,
        kill_participation_1 REAL,
        kill_participation_2 REAL,
        cc_score_1 INTEGER,
        cc_score_2 INTEGER,
        gold_spent_1 INTEGER,
        gold_spent_2 INTEGER,
        PRIMARY KEY (match_id, lane)
    )
    ''')
    conn.commit()
    return conn

def insert_match_record(conn, record):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO match_records 
    (match_id, patch_start, region, lane, champion_1, champion_2, win_1, win_2, kda_1, kda_2, gold_1, gold_2, items_1, items_2,
     damage_dealt_1, damage_dealt_2, damage_taken_1, damage_taken_2, damage_to_objectives_1, damage_to_objectives_2,
     vision_score_1, vision_score_2, cs_1, cs_2, kill_participation_1, kill_participation_2, cc_score_1, cc_score_2,
     gold_spent_1, gold_spent_2)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record.get("match_id"),
        record.get("patch_start"),
        record.get("region"),
        record.get("lane"),
        record.get("champion_1"),
        record.get("champion_2"),
        int(record.get("win_1")),
        int(record.get("win_2")),
        str(record.get("kda_1")),
        str(record.get("kda_2")),
        record.get("gold_1"),
        record.get("gold_2"),
        str(record.get("items_1")),
        str(record.get("items_2")),
        record.get("damage_dealt_1"),
        record.get("damage_dealt_2"),
        record.get("damage_taken_1"),
        record.get("damage_taken_2"),
        record.get("damage_to_objectives_1"),
        record.get("damage_to_objectives_2"),
        record.get("vision_score_1"),
        record.get("vision_score_2"),
        record.get("cs_1"),
        record.get("cs_2"),
        record.get("kill_participation_1"),
        record.get("kill_participation_2"),
        record.get("cc_score_1"),
        record.get("cc_score_2"),
        record.get("gold_spent_1"),
        record.get("gold_spent_2")
    ))
    conn.commit()