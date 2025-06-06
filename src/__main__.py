from chatbot import nexus
from logger import add_user_log, add_nexus_log, get_previous_logs
import os
import threading
from uuid import uuid4
from progress.bar import ChargingBar
from langsmith import traceable

import speech_recognition as sr
import pyttsx3

from utils import listen_to_keyboard


r = sr.Recognizer()
listening = True
exit_event = threading.Event()


def speakText(command):
    """
    The function `speakText` takes a command as input, prints it with "Assistant: " prefix, and then
    uses pyttsx3 library to speak out the command.

    :param command: The `command` parameter in the `speakText` function is a string that represents the
    text that you want the assistant to speak out loud
    """
    print(f"{os.environ.get('name')}: ", command)
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()


thread_id = str(uuid4())
config = {"configurable": {"thread_id": thread_id}}


@traceable
def stream_graph_updates(user_input: str):
    """
    The function `stream_graph_updates` processes user input, interacts with a Nexus service, and
    provides an assistant response.

    :param user_input: The `user_input` parameter in the `stream_graph_updates` function is a string
    that represents the input provided by the user. This input is then processed by the function to
    generate a response from the coding assistant
    :type user_input: str
    """
    global listening
    listening = False
    print("User: ", user_input)
    add_user_log(user_input)
    final_state = nexus.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config)

    assistant_response = final_state["messages"][-1].content
    add_nexus_log(assistant_response)
    speakText(assistant_response)
    listening = True


def load_context():
    """
    The `load_context` function loads previous messages and invokes the NEXUS system with a progress
    bar.
    """
    prior_messages = get_previous_logs()
    progress_bar = ChargingBar(
        f"Initializing NEXUS", max=len(prior_messages)//2)
    for i in range(0, len(prior_messages), 2):  # user, assistant pairs
        history_slice = prior_messages[:i+1]  # include up to current user msg
        nexus.invoke({"messages": history_slice}, config=config)
        progress_bar.next()
    print("\n")


def listen_to_mic():
    """
    The `listen_to_mic` function continuously listens to microphone input, recognizes speech using
    Google's speech recognition, and processes the user input accordingly while handling various
    exceptions.
    """
    while not exit_event.is_set():
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                print("Listening...")
                audio = r.listen(source)
                user_input = r.recognize_google(audio).lower()

                if user_input in ["quit", "exit", "q"]:
                    exit_event.set()
                    break

                stream_graph_updates(user_input)

        except sr.UnknownValueError:
            speakText("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            speakText("Speech recognition failed.")
        except Exception as e:
            speakText("An error occurred.")
            break


def main():
    """
    The main function loads user config, replays logs if specified, and runs an assistant that listens
    to microphone and keyboard inputs.
    """

    # Load and replay logs
    if os.environ.get("retain_memory") != "False":
        load_context()

    # Run the assistant
    mic_thread = threading.Thread(target=listen_to_mic)
    kb_thread = threading.Thread(target=listen_to_keyboard(exit_event))

    mic_thread.start()
    kb_thread.start()

    mic_thread.join()
    kb_thread.join()


if __name__ == "__main__":
    main()
