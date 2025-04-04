# data_parser.py

EARLY_PHASE_THRESHOLD = 600000   # 10 minutes in milliseconds
MID_PHASE_THRESHOLD = 1500000    # 25 minutes in milliseconds

def parse_match_data(match_detail, timeline):
    """
    Parse match details and timeline to extract lane matchups, stats, and item purchase timelines.
    """
    match_info = match_detail.get("info", {})
    game_duration = match_info.get("gameDuration")
    if game_duration is not None and game_duration < 300:
        # Skip remakes or games that are too short to be meaningful
        return []

    participants = match_info.get("participants", [])
    
    # Build mapping from lane to list of participants (ideally two per lane)
    lane_matchups = {}
    for p in participants:
        lane = p.get("teamPosition")
        if not lane:
            continue
        lane_matchups.setdefault(lane, []).append(p)
    
    matchup_records = []
    for lane, players in lane_matchups.items():
        if len(players) == 2:
            record = {}
            p1, p2 = players
            record["lane"] = lane
            record["champion_1"] = p1.get("championName")
            record["champion_2"] = p2.get("championName")
            record["win_1"] = p1.get("win")
            record["win_2"] = p2.get("win")
            record["kda_1"] = (p1.get("kills"), p1.get("deaths"), p1.get("assists"))
            record["kda_2"] = (p2.get("kills"), p2.get("deaths"), p2.get("assists"))
            record["gold_1"] = p1.get("goldEarned")
            record["gold_2"] = p2.get("goldEarned")

            # Damage metrics
            record["damage_dealt_1"] = p1.get("totalDamageDealtToChampions")
            record["damage_dealt_2"] = p2.get("totalDamageDealtToChampions")
            record["damage_taken_1"] = p1.get("totalDamageTaken")
            record["damage_taken_2"] = p2.get("totalDamageTaken")
            record["damage_to_objectives_1"] = p1.get("damageDealtToObjectives")
            record["damage_to_objectives_2"] = p2.get("damageDealtToObjectives")

            # Vision metrics
            vision_score_1 = p1.get("visionScore", 0)
            vision_score_2 = p2.get("visionScore", 0)
            record["vision_score_1"] = round(vision_score_1 / (game_duration / 60), 2) if game_duration else 0
            record["vision_score_2"] = round(vision_score_2 / (game_duration / 60), 2) if game_duration else 0

            # Farming metrics
            cs_1 = p1.get("totalMinionsKilled", 0) + p1.get("neutralMinionsKilled", 0)
            cs_2 = p2.get("totalMinionsKilled", 0) + p2.get("neutralMinionsKilled", 0)
            record["cs_1"] = round(cs_1 / (game_duration / 60), 2) if game_duration else 0
            record["cs_2"] = round(cs_2 / (game_duration / 60), 2) if game_duration else 0

            # Kill participation and other advanced stats
            record["kill_participation_1"] = p1.get("challenges", {}).get("killParticipation")
            record["kill_participation_2"] = p2.get("challenges", {}).get("killParticipation")
            record["cc_score_1"] = p1.get("timeCCingOthers")
            record["cc_score_2"] = p2.get("timeCCingOthers")
            record["gold_spent_1"] = p1.get("goldSpent")
            record["gold_spent_2"] = p2.get("goldSpent")

            # Extract item purchase timeline for each participant
            record["items_1"] = parse_item_events(timeline, p1.get("participantId"))
            record["items_2"] = parse_item_events(timeline, p2.get("participantId"))

            # Compute simple KDA ratios for MVP derivation (using max(deaths, 1) to avoid division by zero)
            kda_ratio_1 = (p1.get("kills", 0) + p1.get("assists", 0)) / max(p1.get("deaths", 1), 1)
            kda_ratio_2 = (p2.get("kills", 0) + p2.get("assists", 0)) / max(p2.get("deaths", 1), 1)
            if kda_ratio_1 > kda_ratio_2:
                record["mvp"] = record.get("champion_1")
            elif kda_ratio_2 > kda_ratio_1:
                record["mvp"] = record.get("champion_2")
            else:
                record["mvp"] = None

            # Derive matchup outcome: assign the winning champion based on the win flags
            record["matchup_outcome"] = record.get("champion_1") if record.get("win_1") else record.get("champion_2")

            matchup_records.append(record)
    return matchup_records

def parse_item_events(timeline, participant_id):
    """
    Parse timeline events to extract item purchase events for a given participant,
    categorizing them into early, mid, or late game based on the timestamp.
    """
    item_events = []
    frames = timeline.get("info", {}).get("frames", [])
    for frame in frames:
        events = frame.get("events", [])
        for event in events:
            event_type = event.get("type")
            if event_type in ["ITEM_PURCHASED", "ITEM_SOLD", "ITEM_UNDO"] and event.get("participantId") == participant_id:
                timestamp = event.get("timestamp")
                if timestamp < EARLY_PHASE_THRESHOLD:
                    phase = "early"
                elif timestamp < MID_PHASE_THRESHOLD:
                    phase = "mid"
                else:
                    phase = "late"
                item_events.append({
                    "itemId": event.get("itemId"),
                    "timestamp": timestamp,
                    "phase": phase,
                    "action": event_type
                })
    return item_events

# TODO: Integrate champion and item name mapping using Data Dragon for enriched data.