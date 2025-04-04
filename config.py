# config.py
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='/Users/wota/Documents/projects/lol/.env')

API_KEY = os.getenv('RIOT_API_KEY')

# Mapping for regions with platform (for summoner/league endpoints) and routing (for match endpoints)
REGIONS = {
    'NA': {'platform': 'na1', 'routing': 'americas'},
    'EUW': {'platform': 'euw1', 'routing': 'europe'},
    'EUNE': {'platform': 'eun1', 'routing': 'europe'},
    'KR': {'platform': 'kr', 'routing': 'asia'},
    'BR': {'platform': 'br1', 'routing': 'americas'},
    'LAN': {'platform': 'la1', 'routing': 'americas'},
    'LAS': {'platform': 'la2', 'routing': 'americas'},
    'OCE': {'platform': 'oc1', 'routing': 'sea'},
    'JP': {'platform': 'jp1', 'routing': 'asia'},
    # Add any additional regions as needed
}

# Ranked Solo/Duo queue ID (420)
RANKED_SOLO_QUEUE_ID = 420

# Define the start of the current patch (Unix timestamp).
# Update this timestamp at each new patch cycle.
CURRENT_PATCH_START = 1743552000  # example timestamp, update per patch