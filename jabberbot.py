import random
import threading
import time

from datetime import datetime

import anki_vector
from anki_vector.exceptions import VectorUnauthenticatedException, VectorUnavailableException, VectorNotFoundException, VectorConnectionException
from anki_vector.events import Events

import config
import context
import events
from functions import debugPrint, not_wake_word_reacting, is_unknown_object
from vector import vector_react

context.init()

def execute_jabberbot(id, stop_thread):

    with anki_vector.Robot(enable_face_detection=True) as robot:

        if not context.is_in_DND_mode:
            vector_react(robot, "greeting")
        else:
            robot.conn.release_control()

        # robot.conn.request_control()
        # robot.behavior.set_eye_color(hue=0.01, saturation=0.99)
        # robot.anim.play_animation("anim_eyepose_furious")
        # robot.conn.release_control()

        dnd_timer = time.time() - 1  # Inital delay for DO-NOT-DISTURB mode report checking

        robot.events.subscribe(events.on_wake_word, Events.wake_word)
        robot.events.subscribe(events.on_robot_state, Events.robot_state)
        robot.events.subscribe(events.on_observed_object, Events.robot_observed_object)
        # robot.events.subscribe(events.on_user_intent, Events.user_intent)

        # with open('animation_names.txt', 'w') as f:
        #   print("List all animation names:", file=f)
        #
        #   for anim_name in robot.anim.anim_list:
        #     print(anim_name, file=f)

        while True:
            try:

                if stop_thread():
                    debugPrint("Stopping Jabberbot while Vector is in his update/restart phase.")
                    return

                if time.time() > dnd_timer:  # Is DND report timer up?

                    context.is_in_DND_mode = not (time.localtime().tm_hour < config.dnd_start and time.localtime().tm_hour >= config.dnd_end)
                    # debugPrint(f"DO-NOT-DISTURB mode check: (start) {time.localtime().tm_hour < config.dnd_start} <-> (end) {config.dnd_end > time.localtime().tm_hour} = {context.is_in_DND_mode}")

                    dnd_timer = time.time() + 300  # Reset timer to only report DND every 5 minutes

                    if context.is_in_DND_mode:
                        # Report that Vector is in DND mode
                        debugPrint(f"Vector is in DO-NOT-DISTURB mode: {config.dnd_start}:00 <-> {config.dnd_end}:00")

                        # Instruct Vector to return to his charger
                        if not robot.status.is_on_charger:
                            debugPrint(f"Vector been told to return to his charger...")
                            robot.conn.request_control()
                            robot.behavior.drive_on_charger()
                            robot.conn.release_control()

                # Outside of DO-NOT-DISTURB mode
                if not context.is_in_DND_mode and not context.is_sleeping and not_wake_word_reacting():
                    # Random chitchat
                    if time.time() > context.chatTimer:
                        reaction = random.choices(["pass", "chat_intro"], [15, 10], k=1)[0]
                        vector_react(robot, reaction)
                        context.chatTimer = time.time() + 30  # Delay timer for random chit-chat.
                        continue

                    # Unknown object detection in range between 10-60mm
                    if time.time() > context.objectTimer and not robot.status.is_docking_to_marker and not robot.status.is_being_held:
                        # We don't want Vector to stop in front of his cube or charger and say "What is this?"
                        if is_unknown_object():
                            # Check for object using Vectors proximity sensor data
                            proximity_data = robot.proximity.last_sensor_reading
                            if proximity_data is not None and proximity_data.found_object and proximity_data.distance.distance_mm in range(10, 60):
                                vector_react(robot, "object_detected")
                                context.objectTimer = time.time() + 30  # Delay for unknown object detection.
                                continue

                    if time.time() > context.faceTimer:
                        # Update saw a face timestamp
                        context.timestamps["last_saw_face"] = datetime.now()

                        try:
                            for face in robot.world.visible_faces:
                                # Did Vector recognize the face?
                                if len(face.name) > 0:
                                    # Save name of the face Vector recognized
                                    context.LAST_FACE_SEEN = face.name
                                    # Update recognized face timestamp
                                    context.timestamps["last_saw_name"] = datetime.now()

                                    debugPrint(f"Vector recognised: {context.LAST_FACE_SEEN}")

                                else:
                                    debugPrint(f"Vector observed an unknown face")

                                reaction = random.choices(["pass", "last_saw_name", "time_intro", "joke_intro", "fact_intro"], [40, 30, 20, 10, 10], k=1)[0]

                                # Disabled due to it not working because "weather_response" is a user intent not an app intent
                                # if reaction == "weather": # show_clock,
                                #     robot.behavior.app_intent(intent="weather_response")
                                # else:
                                vector_react(robot, reaction)
                                break
                        except:
                            time.sleep(1)

                        context.faceTimer = time.time() + 5  # Delay timer for face detection.
                        continue

                    # Check to see if Vector being petted using his touch sensor data
                    touch_data = robot.touch.last_sensor_reading
                    if touch_data is not None and touch_data.is_being_touched:
                        vector_react(robot, "touched")

                # Sleep for a second then loop back (done to limit processor usage)
                time.sleep(1)

            except VectorUnauthenticatedException:
                debugPrint("Vector report an 'Unauthenticated' exception.")
                return
            except VectorUnavailableException:
                debugPrint("Vector report an 'Unavailable' exception.")
                return
            except VectorNotFoundException:
                debugPrint("Vector report an 'Not Found' exception.")
                return
            except VectorConnectionException:
                debugPrint("Vector report an 'Connection' exception.")
                return
            except KeyboardInterrupt:
                debugPrint("Keyboard Interrupt detected.")
                return

# MAIN ******************************************************************************************************************************

def main():
    stop_thread = False
    jabberbot_thread = threading.Thread(target=execute_jabberbot, args=(id, lambda: stop_thread), daemon=True)
    jabberbot_thread.start()

    time.sleep(5)  # Sleep for a moment while the thread starts

    while True:
        try:
            is_in_update_phase = (1 <= time.localtime().tm_hour < 6)

            if is_in_update_phase:
                # We tell the Jabberbot theard to stop while Vector is in his update/restart phase.
                # Without doing this the script will get stuck thinking that it is still connected to Vector
                # even tho connection is lost due to Vector restarting his services.
                stop_thread = True

            elif not is_in_update_phase and not jabberbot_thread.is_alive():
                stop_thread = False
                # Start a new Jabberbot thread now that Vector is outside of his update/restart phase.
                jabberbot_thread = threading.Thread(target=execute_jabberbot, args=(id, lambda: stop_thread), daemon=True)
                jabberbot_thread.start()

            # Sleep for a second then loop back (done to limit processor usage)
            time.sleep(1)

        except KeyboardInterrupt:
            debugPrint("Keyboard Interrupt detected.")
            return

if __name__ == '__main__':
    main()
