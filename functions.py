import json
import random
import time

from datetime import datetime
from math import floor

from gibberish import Gibberish

import context

gibberish = Gibberish()

def debugPrint(info_msg):
    print(datetime.now().strftime("%H:%M:%S.%f").rstrip('0')[:12] + "     " + info_msg)

def loadJSON(file_path, default_data):
    try:
        with open(file_path) as json_file:
            return json.load(json_file)
    except:
        writeJSON(file_path, default_data)
        return default_data

def writeJSON(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=2)

# This takes the line Vector is about to say and replaces anything in curly brackets with either a random word, or the name of the last seen human
# For example: if the dialogue contains "{good}"", then we randomly replace it with a word from the relevant list
def randomizer(to_say):
    # Saw a specific face within last 30 seconds
    faceInView = ("last_saw_name" in context.timestamps and (datetime.now() - context.timestamps["last_saw_name"]).total_seconds() < 30)

    return to_say.format(
        name=context.LAST_FACE_SEEN if faceInView else "",
        good=random.choice(context.GOOD_WORDS),
        interesting=random.choice(context.INTERESTING_WORDS),
        object=random.choice(context.OBJECT_WORDS),
        scary=random.choice(context.SCARY_WORDS),
        swear=random.choice(context.SWEAR_WORDS),
        weird=random.choice(context.WEIRD_WORDS)
    )

def get_chit_chat():
    row = get_unspoken_row("chit_chat", len(context.CHIT_CHAT) - 1)
    return context.CHIT_CHAT[row]

def get_dream():
    row = get_unspoken_row("dreams", len(context.DREAMS) - 1)
    return context.DREAMS[row]

def get_fact():
    row = get_unspoken_row("facts", len(context.FACTS) - 1)
    return context.FACTS[row] + get_fact_end()

def get_fact_end():
    FACT_END = context.DIALOGUE["fact_end"]
    return FACT_END[random.randint(0, len(FACT_END) - 1)]

def get_joke():
    row = get_unspoken_row("jokes", len(context.JOKES) - 1)
    return context.JOKES[row]

# Get the next random row that has been unspoken for the past 20 random rows
def get_unspoken_row(spoken_list, dialogue_row_count):
    row_count = len(context.previously_spoken[spoken_list])
    row_limit = floor(dialogue_row_count / 4)

    row = random.randint(0, dialogue_row_count)
    if row_count > 1:
        while row in context.previously_spoken[spoken_list]:
            row = random.randint(0, dialogue_row_count)

        if row_count == row_limit:
            context.previously_spoken[spoken_list].pop(0)

    context.previously_spoken[spoken_list].append(row)

    # Write away the previously spoken row records at the same time as the timestamps
    writeJSON('previously_spoken.json', context.previously_spoken)

    return row

def random_sentance_generator():
    return ' '.join(gibberish.generate_words(random.randint(3, 6)))

def get_time():
    return time.strftime("%I:%M %p")

def reset_timers():
    context.chargingTimer = time.time() + 60  # Delay timer for on charger.
    context.heldTimer = time.time() + 5  # Delay timer for been picked up.
    context.faceTimer = time.time() + 30  # Delay timer for face detection.
    context.chatTimer = time.time() + 30  # Delay timer for random chit-chat.
    context.objectTimer = time.time() + 30  # Delay for unknown object detection.
