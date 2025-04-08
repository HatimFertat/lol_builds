import sqlite3

def init_db(db_path="data/matches.db"):
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
        champion_transform_1 TEXT,
        champion_transform_2 TEXT,
        individual_position_1 TEXT,
        individual_position_2 TEXT,
        team_id_1 INTEGER,
        team_id_2 INTEGER,
        bounty_level_1 INTEGER,
        bounty_level_2 INTEGER,
        physical_damage_dealt_1 INTEGER,
        physical_damage_dealt_2 INTEGER,
        magic_damage_dealt_1 INTEGER,
        magic_damage_dealt_2 INTEGER,
        true_damage_dealt_1 INTEGER,
        true_damage_dealt_2 INTEGER,
        physical_damage_taken_1 INTEGER,
        physical_damage_taken_2 INTEGER,
        magic_damage_taken_1 INTEGER,
        magic_damage_taken_2 INTEGER,
        true_damage_taken_1 INTEGER,
        true_damage_taken_2 INTEGER,
        total_damage_dealt_1 INTEGER,
        total_damage_dealt_2 INTEGER,
        damage_self_mitigated_1 INTEGER,
        damage_self_mitigated_2 INTEGER,
        turret_takedowns_1 INTEGER,
        turret_takedowns_2 INTEGER,
        dragon_takedowns_1 INTEGER,
        dragon_takedowns_2 INTEGER,
        baron_takedowns_1 INTEGER,
        baron_takedowns_2 INTEGER,
        longest_time_living_1 INTEGER,
        longest_time_living_2 INTEGER,
        champ_experience_1 INTEGER,
        champ_experience_2 INTEGER,
        time_played_1 INTEGER,
        time_played_2 INTEGER,
        match_duration INTEGER,
        first_blood_kill_1 BOOLEAN,
        first_blood_kill_2 BOOLEAN,
        first_blood_assist_1 BOOLEAN,
        first_blood_assist_2 BOOLEAN,
        gold_per_minute_1 REAL,
        gold_per_minute_2 REAL,
        xp_diff_per_minute_1 REAL,
        xp_diff_per_minute_2 REAL,
        ally_champions_1 TEXT,
        ally_champions_2 TEXT,
        enemy_champions_1 TEXT,
        enemy_champions_2 TEXT,
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
     gold_spent_1, gold_spent_2, champion_transform_1, champion_transform_2, individual_position_1, individual_position_2,
     team_id_1, team_id_2, bounty_level_1, bounty_level_2, physical_damage_dealt_1, physical_damage_dealt_2,
     magic_damage_dealt_1, magic_damage_dealt_2, true_damage_dealt_1, true_damage_dealt_2, physical_damage_taken_1,
     physical_damage_taken_2, magic_damage_taken_1, magic_damage_taken_2, true_damage_taken_1, true_damage_taken_2,
     total_damage_dealt_1, total_damage_dealt_2, damage_self_mitigated_1, damage_self_mitigated_2, turret_takedowns_1,
     turret_takedowns_2, dragon_takedowns_1, dragon_takedowns_2, baron_takedowns_1, baron_takedowns_2,
     longest_time_living_1, longest_time_living_2, champ_experience_1, champ_experience_2, time_played_1, time_played_2,
     match_duration, first_blood_kill_1, first_blood_kill_2, first_blood_assist_1, first_blood_assist_2,
     gold_per_minute_1, gold_per_minute_2, xp_diff_per_minute_1, xp_diff_per_minute_2, ally_champions_1,
     ally_champions_2, enemy_champions_1, enemy_champions_2)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        record.get("gold_spent_2"),
        record.get("champion_transform_1"),
        record.get("champion_transform_2"),
        record.get("individual_position_1"),
        record.get("individual_position_2"),
        record.get("team_id_1"),
        record.get("team_id_2"),
        record.get("bounty_level_1"),
        record.get("bounty_level_2"),
        record.get("physical_damage_dealt_1"),
        record.get("physical_damage_dealt_2"),
        record.get("magic_damage_dealt_1"),
        record.get("magic_damage_dealt_2"),
        record.get("true_damage_dealt_1"),
        record.get("true_damage_dealt_2"),
        record.get("physical_damage_taken_1"),
        record.get("physical_damage_taken_2"),
        record.get("magic_damage_taken_1"),
        record.get("magic_damage_taken_2"),
        record.get("true_damage_taken_1"),
        record.get("true_damage_taken_2"),
        record.get("total_damage_dealt_1"),
        record.get("total_damage_dealt_2"),
        record.get("damage_self_mitigated_1"),
        record.get("damage_self_mitigated_2"),
        record.get("turret_takedowns_1"),
        record.get("turret_takedowns_2"),
        record.get("dragon_takedowns_1"),
        record.get("dragon_takedowns_2"),
        record.get("baron_takedowns_1"),
        record.get("baron_takedowns_2"),
        record.get("longest_time_living_1"),
        record.get("longest_time_living_2"),
        record.get("champ_experience_1"),
        record.get("champ_experience_2"),
        record.get("time_played_1"),
        record.get("time_played_2"),
        record.get("match_duration"),
        int(record.get("first_blood_kill_1", 0)),
        int(record.get("first_blood_kill_2", 0)),
        int(record.get("first_blood_assist_1", 0)),
        int(record.get("first_blood_assist_2", 0)),
        record.get("gold_per_minute_1"),
        record.get("gold_per_minute_2"),
        record.get("xp_diff_per_minute_1"),
        record.get("xp_diff_per_minute_2"),
        str(record.get("ally_champions_1")),
        str(record.get("ally_champions_2")),
        str(record.get("enemy_champions_1")),
        str(record.get("enemy_champions_2"))
    ))
    conn.commit()