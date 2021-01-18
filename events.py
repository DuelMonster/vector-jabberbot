import random
import time

from datetime import datetime
from math import ceil

import functions
import context

from vector import vector_react, vector_sleep

picked_up_block = False

# Wake Word Event handler
def on_wake_word(robot, event_type, event):
    if not context.is_in_DND_mode and not context.is_sleeping:
        vector_react(robot, "wake_word")

    return

# Object Detection Event handler
def on_observed_object(robot, event_type, event):
    if not context.is_in_DND_mode and not context.is_sleeping:

        # Ensure it has been at least 10 seconds since someone used Vector's wake word
        if event.object_family == "LIGHT_CUBE":
            if "wake_word" not in context.timestamps or (datetime.now() - context.timestamps["wake_word"]).total_seconds() > 10:
                vector_react(robot, "cube_detected")

        # elif event.object_family != "CHARGER":
        #     functions.debugPrint(f"observed_object: {event}")

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

    if not context.is_in_DND_mode and not context.is_sleeping:

        # Vectors is on his charger
        if robot.status.is_on_charger and time.time() > context.chargingTimer:
            # If Vector is fully charged and has been on his charger for sometime, have him drive off
            if robot.get_battery_state().battery_level == 3 and time.time() > context.restTimer:
                fully_charged_intent = "explore_start"  # random.choices([
                #     "explore_start",
                #     "play_pickupcube",
                #     "play_rollcube",
                #     "play_popawheelie",
                #     "play_fistbump",
                #     "imperative_findcube",
                #     "imperative_fetchcube"
                # ],
                #     [50, 20, 20, 20, 10, 15, 10],
                #     k= 1
                # )[0]

                functions.debugPrint(f"Vector is well rested and was told to '{fully_charged_intent}'...")

                # robot.conn.request_control()
                robot.behavior.app_intent(intent=fully_charged_intent)  # Sometimes Vector will ignore this request, not sure why...
                # async_future = # async_future.result()
                # robot.conn.release_control()

                context.restTimer = time.time() + random.randint(600, 1200)  # Delay timer for randomising time spent on charger.

            else:
                vector_react(robot, "charging")
                context.chargingTimer = time.time() + 60  # Delay timer for on charger.

                if robot.get_battery_state().battery_level < 3 and (context.restTimer - time.time()) < 0:
                    context.restTimer = time.time() + random.randint(600, 1200)  # Delay timer for randomising time spent on charger.

                # functions.debugPrint(f"Battery Level: {robot.get_battery_state().battery_level}")
                functions.debugPrint(f"Rest Time Remaining: {ceil((context.restTimer - time.time()) / 60)}")

        # Vectors battery needs charging - *** This currently doesn't work due to Vector performing his return to charger event
        # elif not robot.status.is_on_charger and robot.get_battery_state().battery_level <= 1:
        #     vector_react(robot, "needs_charging")

        # Vectors is in calm power mode
        elif robot.status.is_in_calm_power_mode and robot.status.is_on_charger:
            vector_react(robot, "sleeping")

        # Vectors has been picked up
        elif robot.status.is_being_held and time.time() > context.heldTimer:
            vector_react(robot, "picked_up")
            context.heldTimer = time.time() + 5  # Delay timer for been picked up.

        # Vectors detected an edge
        elif robot.status.is_cliff_detected and not robot.status.is_being_held:
            vector_react(robot, "cliff")

        # Vector dropped his block
        elif not robot.status.is_carrying_block and picked_up_block:
            vector_react(robot, "dropped_block")
            picked_up_block = False

        # Vector picked up his block
        elif robot.status.is_carrying_block:
            picked_up_block = robot.status.is_carrying_block

        # Vectors button has been pressed
        elif robot.status.is_button_pressed:
            vector_react(robot, "button_pressed")

    return


# Observed Face Event handler
#
# event_type == 'robot_observed_face'
# event = {
#   face_id: 4
#   timestamp: 36249060
#   pose {
#     x: -337.34503
#     y: -641.58594
#     z: 391.15607
#     q0: 0.9454563
#     q1: 0.31855205
#     q2: -0.0668846
#     q3: 0.01278025
#     origin_id: 18
#   }
#   img_rect {
#     x_top_left: 261.0
#     y_top_left: 88.0
#     width: 120.0
#     height: 120.0
#   }
# }
#
# event_type == 'robot_changed_observed_face_id'
# event = {
#   old_id: -2
#   new_id: 3
# }
#
def on_observed_face(robot, event_type, event):

    # Vector saw a face, and the timer for random comments is up (they are weighted, with "pass" for 'do nothing')
    if context.is_in_DND_mode == False and context.is_sleeping == False and time.time() > context.faceTimer:
        # Update saw a face timestamp
        context.timestamps["last_saw_face"] = datetime.now()

        face = robot.world.get_face(event.new_id if event_type == 'robot_changed_observed_face_id' else event.face_id)

        # Did Vector recognize the face?
        if len(face.name) > 0:
            # Save name of the face Vector recognized
            context.LAST_FACE_SEEN = face.name
            # Update recognized face timestamp
            context.timestamps["last_saw_name"] = datetime.now()

        functions.debugPrint(f"Vector observed face: {context.LAST_FACE_SEEN}")

        reaction = random.choices(["pass", "joke_intro", "fact_intro", "time_intro", "last_saw_name"], [50, 10, 10, 15, 30], k=1)[0]

        vector_react(robot, reaction)
        context.faceTimer = time.time() + 30  # Delay timer for face detection.

        # show_clock, weather_response

    return
