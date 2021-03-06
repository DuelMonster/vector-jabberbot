import random
import time

from datetime import datetime
from math import ceil

from anki_vector.events import Events

import functions
import context

from vector import vector_react, vector_sleep

picked_up_block = False

# Wake Word Event handler
def on_wake_word(robot, event_type, event):
    if not context.is_in_DND_mode and not context.is_sleeping:
        vector_react(robot, "wake_word")  # Only done to record timestamp

    return

# Object Detection Event handler
def on_observed_object(robot, event_type, event):
    if not context.is_in_DND_mode and not context.is_sleeping:
        # Ensure it has been at least 30 seconds since someone used Vector's wake word
        if functions.not_wake_word_reacting():
            proximity_data = robot.proximity.last_sensor_reading
            if proximity_data is not None and proximity_data.found_object and proximity_data.distance.distance_mm in range(10, 120):

                if event.object_family == context.OBJECT_FAMILY.LIGHT_CUBE:
                    vector_react(robot, "cube_detected")

                elif event.object_family == context.OBJECT_FAMILY.CHARGER:
                    vector_react(robot, "charger_detected")

                else:
                    functions.debugPrint(f"observed_object: {event}")

    return

# Voice Command Processed Event handler
# def on_user_intent(robot, event_type, event):
#     if not context.is_in_DND_mode and not context.is_sleeping:
#         functions.debugPrint(f"user_intent:\n{event}")
#         # vector_react(robot, "user_intent")

#     return

# State Changed Event handler
def on_robot_state(robot, event_type, event):
    global picked_up_block

    if not context.is_in_DND_mode and not context.is_sleeping and functions.not_wake_word_reacting():

        battery_state = robot.get_battery_state()

        # Vectors is on his charger
        if robot.status.is_on_charger:
            # If Vector is fully charged and has been on his charger for sometime, have him drive off
            if battery_state.battery_level == 3 and time.time() > context.restTimer:
                fully_charged_app_intent = random.choices([
                    "explore_start",
                    "intent_imperative_come",
                    "intent_imperative_dance",
                    "intent_imperative_fetchcube",
                    "intent_imperative_findcube",
                    "intent_imperative_lookatme"
                ], [30, 20, 20, 20, 20, 20], k=1)[0]

                time.sleep(random.randint(120, 600))  # remain on charger for a random time before driving off

                if robot.status.is_on_charger:  # check Vector is still on the charger and hasn't been moved or removed himself
                    functions.debugPrint(f"Vector is well rested and was told to '{fully_charged_app_intent}'...")

                    robot.behavior.app_intent(intent=fully_charged_app_intent)  # Sometimes Vector will ignore this request, not sure why...

                    # Reset the various timers to ensure that the app_intent isn't interupted
                    functions.reset_timers()

            elif time.time() > context.chargeTimer:

                functions.debugPrint(f"Rest Time Remaining: {ceil((context.restTimer - time.time()) / 60)}")
                context.chargeTimer = time.time() + 20  # Delay timer for on charger.

                if battery_state.battery_level < 3 and time.time() > context.restTimer:
                    context.restTimer = time.time() + random.randint(900, 3600)  # Delay timer for randomising time spent on charger.

                # Vectors is in calm power mode
                if robot.status.is_in_calm_power_mode:
                    vector_react(robot, "sleeping")
                else:
                    vector_react(robot, "charging")

        # Check battery levels
        elif not robot.status.is_on_charger and time.time() > context.chargeTimer:

            context.chargeTimer = time.time() + 20  # Delay timer for on charger.

            # Vectors battery needs charging
            # battery_state.battery_level will report as 1 below 3.6 volts and Vectors return to charger event will be triggered.
            # So we react to the low level before Vector can, by checking for a voltage of 3.605 or lower
            if battery_state.battery_volts <= 3.605:
                vector_react(robot, "needs_charging")
                functions.debugPrint(f"Battery Volts: {battery_state.battery_volts}")

            # Vectors Cube battery needs charging
            elif battery_state.cube_battery.level == 1:
                vector_react(robot, "cube_battery")
                functions.debugPrint(f"Cube battery Volts: {battery_state.cube_battery.battery_volts}")

        # Vectors has been picked up
        elif robot.status.is_being_held and time.time() > context.heldTimer:
            vector_react(robot, "picked_up")
            context.heldTimer = time.time() + 5  # Delay timer for been picked up.

        # Vectors detected an edge
        elif robot.status.is_cliff_detected and not robot.status.is_being_held:
            vector_react(robot, "cliff")

        # Vector picked up his block
        elif robot.status.is_carrying_block:
            picked_up_block = robot.status.is_carrying_block

        # Vector dropped his block
        elif not robot.status.is_carrying_block and picked_up_block:
            vector_react(robot, "dropped_block")
            picked_up_block = False

        # Vectors button has been pressed
        elif robot.status.is_button_pressed:
            vector_react(robot, "button_pressed")

        # else:
        #     functions.debugPrint(f"{event_type}:\n{event}")

    return
