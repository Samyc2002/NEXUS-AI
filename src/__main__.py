import os
from uuid import uuid4
from progress.bar import ChargingBar
from langsmith import traceable

import speech_recognition as sr
import pyttsx3

from chatbot import nexus
from logger import add_user_log, add_nexus_log, get_previous_logs
from utils import load_config

r = sr.Recognizer()
listening = True


def speakText(command):
    """
    The function `speakText` takes a command as input, prints it with "Assistant: " prefix, and then
    uses pyttsx3 library to speak out the command.

    :param command: The `command` parameter in the `speakText` function is a string that represents the
    text that you want the assistant to speak out loud
    """
    print("Assistant: ", command)
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


def main():
    """
    The main function continuously listens for user input, processes it, and handles exceptions
    accordingly.
    """
    # Load user config
    load_config()

    # Load and replay logs
    if os.environ.get("retain_memory") == "true":
        load_context()

    # Run the assistant
    while True:
        if listening:
            print("Listening...")
        try:
            with sr.Microphone() as source2:
                r.adjust_for_ambient_noise(source2, duration=0.2)
                audio2 = r.listen(source2)
                user_input = r.recognize_google(audio2)
                user_input = user_input.lower()
                if user_input in ["quit", "exit", "q"]:
                    break
                stream_graph_updates(user_input)
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))
            speakText("Sorry I messed up in my search. Can you please repeat?")
        except sr.UnknownValueError:
            speakText("Sorry I didn't get you. Can you please repeat?")
        except:
            break


if __name__ == "__main__":
    main()
