import json

EARLY_PHASE_THRESHOLD = 600000   # 10 minutes in milliseconds
MID_PHASE_THRESHOLD = 1500000    # 25 minutes in milliseconds

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
            if event_type in ["ITEM_PURCHASED", "ITEM_SOLD", "ITEM_UNDO", "ITEM_DESTROYED"] and event.get("participantId") == participant_id:
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

with open("tests/timeline.json", "r") as file:
    timeline = json.load(file)

item_events = parse_item_events(timeline, participant_id=2)

print(item_events)