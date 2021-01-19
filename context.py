import csv
import random
import time

from datetime import datetime, timedelta
from enum import Enum, IntEnum

from anki_vector import audio

import config
from functions import loadJSON, writeJSON

from lists.chit_chat import CHIT_CHAT
from lists.dialogue import DIALOGUE
from lists.dreams import DREAMS
from lists.facts import FACTS
from lists.jokes import JOKES

# List for use by the randomizer function
from lists.synonyms.good_synonyms import GOOD_WORDS
from lists.synonyms.interesting_synonyms import INTERESTING_WORDS
from lists.synonyms.object_synonyms import OBJECT_WORDS
from lists.synonyms.scary_synonyms import SCARY_WORDS
from lists.synonyms.swear_word_synonyms import SWEAR_WORDS
from lists.synonyms.weird_synonyms import WEIRD_WORDS

VERSION = "0.1.4"

def init():
    global timestamps
    timestamps = {}

    # Load the timestamps from file. Create a new one if not found.
    try:
        with open('timestamps.csv', mode='r') as csv_file:
            timestamps = dict(filter(None, csv.reader(csv_file)))
    except:
        with open('timestamps.csv', 'w', newline='') as csv_file:
            csv.writer(csv_file)

    # Convert strings from CSV to datetime objects
    for key, value in timestamps.items():
        timestamps[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    global LAST_FACE_SEEN
    LAST_FACE_SEEN = ""

    global is_in_DND_mode
    is_in_DND_mode = False

    global is_sleeping
    is_sleeping = False

    global is_reacting
    is_reacting = False

    # Previously spoken row records
    global previously_spoken
    previously_spoken = loadJSON('previously_spoken.json', default_data={"chit_chat": [], "dreams": [], "facts": [], "jokes": []})

    # Initialise random reation timers
    global chargeTimer, chatTimer, faceTimer, heldTimer, objectTimer, restTimer
    chargeTimer = time.time() + 5  # Delay timer for on charger.
    chatTimer = time.time() + 30     # Delay timer for random chit-chat.
    faceTimer = time.time() + 5      # Delay timer for face detection.
    heldTimer = time.time() + 5      # Delay timer for been picked up.
    objectTimer = time.time() + 30   # Inital delay for unknown object detection.
    restTimer = time.time()          # Delay timer for randomising time spent on charger.

# Function to save the timestamps (when an event/trigger happened, and when it can happen next)
def update_timestamp(react_to, to_add_override=0):
    to_add = to_add_override

    if not to_add_override > 0 and react_to in DIALOGUE.keys():
        reaction = DIALOGUE[react_to]

        min_delay = int(int(reaction["minimum_delay"]) * CHATTINESS)  # Get the minimum delay and adjust by CHATTINESS
        max_delay = int(int(reaction["maximum_delay"]) * CHATTINESS)  # Get the maximum delay and adjust by CHATTINESS
        to_add = random.randint(min_delay, max_delay)

    timestamps[react_to + "_next"] = datetime.now() + timedelta(seconds=to_add)  # Update timestamps with the next time Vector will be able to speak on that event/trigger
    timestamps[react_to] = datetime.now()  # Update the event in timestamps so I have a timestamp for when event/trigger occurred

    # functions.debugPrint(f"Adding {to_add} seconds to {react_to}.")

    save_timestamps()

def save_timestamps():
    with open('timestamps.csv', 'w', newline='') as csv_file:
        timestamp_writer = csv.writer(csv_file)
        for key, value in timestamps.items():
            timestamp_writer.writerow([key, datetime.strftime(value, "%Y-%m-%d %H:%M:%S")])

# These are multipliers for the chattiness setting (they raise or lower the time delays)
MULTIPLIERS = {
    1: 6,
    2: 4,
    3: 2,
    4: 1.5,
    5: 1,
    6: 0.8,
    7: 0.6,
    8: 0.4,
    9: 0.2,
    10: 0.1
}

CHATTINESS = MULTIPLIERS[config.chattiness]

# In the config file users can set a volume (1-5) for Vector's voice and sounds
VOL = {
    1: audio.RobotVolumeLevel.LOW,
    2: audio.RobotVolumeLevel.MEDIUM_LOW,
    3: audio.RobotVolumeLevel.MEDIUM,
    4: audio.RobotVolumeLevel.MEDIUM_HIGH,
    5: audio.RobotVolumeLevel.HIGH
}

# Vectors default Objects
class OBJECT_FAMILY(IntEnum):
    LIGHT_CUBE = 3
    CHARGER = 4


# After Vector tells a joke he randomly plays one of these animation triggers
JOKE_ANIM = [
    "GreetAfterLongTime",
    "ComeHereSuccess",
    "OnboardingReactToFaceHappy",
    "PickupCubeSuccess",
    "PounceSuccess",
    "ConnectToCubeSuccess",
    "FetchCubeSuccess",
    "FistBumpSuccess",
    "OnboardingWakeWordSuccess"
]

SLEEP_ANIM = [
    "anim_gotosleep_sleeping_01",
    "anim_gotosleep_sleeping_02",
    "anim_gotosleep_sleeping_03",
    "anim_gotosleep_sleeping_04",
    "anim_gotosleep_sleeping_05",
    "anim_gotosleep_sleeploop_01"
]
