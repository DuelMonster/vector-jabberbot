import random
import time

from datetime import datetime, timedelta
from math import ceil

import config
import functions
import context

# Fuction used to have Vector react to different events/triggers
def vector_react(robot, react_to):

    if react_to == "pass":  # This adds some randomness to how often Vector will react to events/trigers
        functions.debugPrint("Instead of attempting a random comment, I chose to pass this time...")
        return

    if robot.status.is_pathing:  # If Vector is busy doing something, don't speak
        functions.debugPrint("Vector is pathing...")
        return

    now = datetime.now()

    if react_to not in context.timestamps:
        context.timestamps[react_to] = now - timedelta(seconds=100)  # Fixes problem for new installs where Vector thinks everything JUST happened
        context.timestamps[react_to + "_next"] = now + timedelta(seconds=random.randint(6, 24))  # Don't want him trying to say everything at once

    if now > context.timestamps[react_to + "_next"]:  # If the time for the [event/trigger]_next timestamp has passed, that event is available
        functions.debugPrint(f"Vector is trying to react to: {react_to}")

        if react_to == "sleeping":
            vector_sleep(robot)

        else:
            if react_to in context.DIALOGUE.keys():
                reaction = context.DIALOGUE[react_to]

                min_delay = int(int(reaction["minimum_delay"]) * context.CHATTINESS)  # Get the minimum delay and adjust by CHATTINESS
                max_delay = int(int(reaction["maximum_delay"]) * context.CHATTINESS)  # Get the maximum delay and adjust by CHATTINESS
                to_add = random.randint(min_delay, max_delay)

                functions.debugPrint(f"Adding {to_add} seconds to {react_to}.")

                context.timestamps[react_to + "_next"] = now + timedelta(seconds=to_add)  # Update timestamps with the next time Vector will be able to speak on that event/trigger
                context.timestamps[react_to] = datetime.now()  # Update the event in timestamps so I have a timestamp for when event/trigger occurred

                context.save_timestamps()

                vector_say(robot, react_to)

    else:
        functions.debugPrint(f"Vector isn't ready to talk about {react_to} yet.")

    return

# This makes Vector talk by looking up dialogue in the dlg file
def vector_say(robot, arg_say):
    to_say = ''

    if arg_say in context.DIALOGUE.keys():
        reaction = context.DIALOGUE[arg_say]
        if "lines" in reaction.keys() and len(reaction["lines"]) > 0:
            to_say = reaction["lines"][random.randint(0, len(reaction["lines"]) - 1)]

    if arg_say == "wake_word":
        return  # If wake_word then skip talking for a bit
    if arg_say == "joke_intro":
        to_say = to_say + functions.get_joke()  # if joke then add to end of intro
    if arg_say == "fact_intro":
        to_say = to_say + functions.get_fact()  # if fact then add to end of intro
    if arg_say == "time_intro":
        to_say = to_say + functions.get_time()  # Randomly announce the time
    if arg_say == "chat_intro":
        to_say = to_say + functions.get_chit_chat()  # Randomly announce the time

    to_say = functions.randomizer(to_say)  # This replaces certain words with synonyms

    max_attempts = 15
    current_attempts = 1

    while current_attempts < max_attempts:
        current_attempts += 1
        try:
            robot.conn.request_control()

            robot.audio.set_master_volume(context.VOL[config.voice_volume])  # Change voice volume to config setting

            functions.debugPrint(f"Vector says: '{to_say}'")
            robot.behavior.say_text(to_say, duration_scalar=1.15)  # Slow the voice down slightly to make him easier to understand

            if arg_say == "joke_intro":
                robot.anim.play_animation_trigger(random.choice(context.JOKE_ANIM))  # If a joke, play a random animation trigger

            robot.audio.set_master_volume(context.VOL[config.sound_volume])  # Change sound effects volume back to config setting
            robot.conn.release_control()

            return
        except:
            functions.debugPrint(f"Couldn't get control of robot. Trying again...")
            time.sleep(1)

    if current_attempts >= max_attempts:
        functions.debugPrint("Error getting control")

    return

# Start Vector on a randomly generated sleep cycle
def vector_sleep(robot):

    context.is_sleeping = True

    # Set a random total sleep timer between 5-20 minutes
    sleepDuration = random.randint(300, 1200)
    sleepTimer = time.time() + sleepDuration

    functions.debugPrint(f"Okay, I am going into REM sleep now for {ceil(sleepDuration / 60)} mins...")

    robot.conn.request_control()

    robot.audio.set_master_volume(context.VOL[1])
    robot.anim.play_animation('anim_gotosleep_getin_01')  # Replay the going to sleep animation because requesting control will wake Vector up again

    # Give Vector a random sleep cycle
    while time.time() < sleepTimer:

        time.sleep(random.randint(60, 300))

        dream = random.choices([functions.random_sentance_generator(), functions.get_dream()], [10, 10], k=1)[0]

        functions.debugPrint(f"Vector is dreaming: '{dream}'")

        robot.behavior.say_text(dream, duration_scalar=1.95)  # Slow down Vectors speach so it sounds like he is dreaming
        robot.anim.play_animation(context.SLEEP_ANIM[random.randint(0, len(context.SLEEP_ANIM) - 1)])  # Play a random sleep animation

    # Wake Vector up after his little nap
    robot.anim.play_animation("anim_gotosleep_wakeup_01")
    robot.audio.set_master_volume(context.VOL[config.voice_volume])
    vector_say(robot, "wake_up")
    robot.audio.set_master_volume(context.VOL[config.sound_volume])

    robot.conn.release_control()

    context.is_sleeping = False

    # Reset the various timers to ensure Vector doesn't speak straight after waking up
    functions.reset_timers()

    return
