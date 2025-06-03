from langsmith import traceable

import speech_recognition as sr
import pyttsx3

from .chatbot import nexus
from .logger import add_user_log, add_nexus_log


r = sr.Recognizer()


def speakText(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()


config = {"configurable": {"thread_id": "1"}}


@traceable
def stream_graph_updates(user_input: str):
    add_user_log(user_input)
    final_state = nexus.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config)

    assistant_response = final_state["messages"][-1].content
    add_nexus_log(assistant_response)
    speakText(assistant_response)


while True:
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
