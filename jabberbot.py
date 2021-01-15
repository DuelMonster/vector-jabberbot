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
from functions import debugPrint
from vector import vector_react

context.init()

def execute_jabberbot(id, stop_thread):

    with anki_vector.Robot(enable_face_detection=True) as robot:

        if not context.is_in_DND_mode:
            vector_react(robot, "greeting")

        # robot.conn.request_control()
        # robot.behavior.set_eye_color(hue=0.01, saturation=0.99)
        # robot.anim.play_animation("anim_eyepose_furious")
        # robot.conn.release_control()

        dnd_timer = time.time()  # Inital delay for DO-NOT-DISTURB mode report checking

        robot.events.subscribe(events.on_wake_word, Events.wake_word)
        robot.events.subscribe(events.on_robot_state, Events.robot_state)
        robot.events.subscribe(events.on_observed_face, Events.robot_observed_face)
        robot.events.subscribe(events.on_observed_face, Events.robot_changed_observed_face_id)
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

                elif config.dnd_end <= time.localtime().tm_hour < config.dnd_start:  # Outside of DO-NOT-DISTURB mode
                    if context.is_in_DND_mode:  # Reset flags if DND mode ended
                        context.is_in_DND_mode = False
                        context.is_sleeping = False

                    if not context.is_sleeping:
                        # Random chitchat
                        if time.time() > context.chatTimer:
                            reaction = random.choices(["pass", "chat_intro"], [15, 10], k=1)[0]
                            vector_react(robot, reaction)
                            context.chatTimer = time.time() + 30  # Delay timer for random chit-chat.

                        # Unknown object detection in range between 10-60mm
                        elif time.time() > context.objectTimer and not robot.status.is_docking_to_marker and not robot.status.is_being_held:
                            # We don't want Vector to stop in front of his cube and say "What is this?"
                            if "cube_detected" not in context.timestamps or (datetime.now() - context.timestamps["cube_detected"]).total_seconds() > 10:
                                # Check for object using Vectors proximity sensor data
                                proximity_data = robot.proximity.last_sensor_reading
                                if proximity_data is not None and proximity_data.found_object and robot.proximity.last_sensor_reading.distance.distance_mm in range(10, 60):
                                    vector_react(robot, "object_detected")
                                    context.objectTimer = time.time() + 30  # Inital delay for unknown object detection.

                        # Check to see if Vector being petted using his touch sensor data
                        touch_data = robot.touch.last_sensor_reading
                        if touch_data is not None and touch_data.is_being_touched:
                            vector_react(robot, "touched")

                elif time.time() > dnd_timer:  # Is DND report timer up?

                    # If Vector isn't aready sleeping instruct him to go to sleep using his default sleep routine.
                    if not context.is_sleeping:
                        context.is_sleeping = True

                        # robot.conn.request_control()
                        robot.behavior.app_intent(intent="greeting_goodnight")  # Sometimes Vector will ignore this request, not sure why...
                        # robot.conn.release_control()

                    # Report that Vector is in DND mode
                    debugPrint(f"Vector is in DO-NOT-DISTURB mode...  {config.dnd_start}:00 <-> {config.dnd_end}:00")
                    context.is_in_DND_mode = True
                    dnd_timer = time.time() + 300  # Reset timer to only report DND every 5 minutes

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
            is_in_update_phase = (11 <= time.localtime().tm_hour < 12)

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
