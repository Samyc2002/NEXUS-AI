

import time
import torch
import sounddevice as sd
import numpy as np
from queue import Queue, Empty
from utils import listen_to_keyboard
import pyttsx3
import speech_recognition as sr
from langsmith import traceable
from progress.bar import ChargingBar
from uuid import uuid4
import threading
import os
from logger import add_user_log, add_nexus_log, get_previous_logs
from chatbot import nexus
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

# Globals
r = sr.Recognizer()
exit_event = threading.Event()

# Load Silero VAD model once
vad_model = load_silero_vad()

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5  # seconds per audio chunk to process


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
    print("User: ", user_input)
    add_user_log(user_input)
    final_state = nexus.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config)

    assistant_response = final_state["messages"][-1].content
    add_nexus_log(assistant_response)
    speakText(assistant_response)


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


def audio_callback(indata, frames, time, status):
    """Called by sounddevice for each audio chunk from mic"""
    if status:
        print(f"Sounddevice status: {status}")
    q.put(indata.copy())


def listen_to_mic():
    """
    Continuously listens to microphone input, uses Silero VAD to detect speech,
    then runs Google speech recognition on detected speech segments,
    and handles quit commands.
    """
    print("Starting mic listener...")
    global q
    q = Queue()
    
    # Track when we last processed speech to avoid rapid repeated messages
    last_speech_time = 0
    min_time_between_messages = 2  # seconds

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=audio_callback):
        buffer = np.zeros((0, CHANNELS), dtype='int16')

        while not exit_event.is_set():
            try:
                # Collect audio chunks from queue
                data = q.get(timeout=1)  # wait for max 1 sec

                # Append new data to buffer
                buffer = np.concatenate((buffer, data), axis=0)

                # Convert buffer to torch tensor and normalize to float32 (-1.0 to 1.0)
                waveform = torch.from_numpy(
                    buffer.T.astype(np.float32) / 32768.0)

                # Run VAD on the buffered audio with more aggressive parameters
                speech_timestamps = get_speech_timestamps(
                    waveform, 
                    vad_model, 
                    sampling_rate=SAMPLE_RATE,
                    min_speech_duration_ms=250,     # Minimum speech segment duration
                    max_speech_duration_s=float('inf'),  # No maximum duration
                    min_silence_duration_ms=1000,   # Increased to 1000ms (1 second)
                    speech_pad_ms=500,              # Increased padding to 500ms
                    threshold=0.3                    # Lower threshold to be more sensitive
                )

                if speech_timestamps:
                    # Calculate average speech probability to filter out weak detections
                    # This helps avoid processing background noise
                    speech_probs = []
                    for seg in speech_timestamps:
                        start, end = seg['start'], seg['end']
                        # Get the segment and calculate its energy/volume
                        segment = waveform[:, start:end]
                        energy = torch.mean(torch.abs(segment)).item()
                        speech_probs.append(energy)
                    
                    avg_speech_prob = sum(speech_probs) / len(speech_probs) if speech_probs else 0
                    
                    # Only process if the speech probability is high enough
                    # and enough time has passed since the last message
                    current_time = time.time()
                    if avg_speech_prob > 0.01 and (current_time - last_speech_time) >= min_time_between_messages:
                        # Wait a bit after detecting speech to capture more audio
                        # This helps ensure we get the complete phrase
                        try:
                            # Try to get more audio data for up to 1.5 seconds after speech detection
                            wait_end = time.time() + 1.5
                            while time.time() < wait_end:
                                try:
                                    more_data = q.get(timeout=0.1)
                                    buffer = np.concatenate((buffer, more_data), axis=0)
                                except Empty:
                                    continue
                        except Exception:
                            pass  # If any error occurs during waiting, just proceed with what we have
                            
                        # Update waveform with new buffer data
                        waveform = torch.from_numpy(buffer.T.astype(np.float32) / 32768.0)
                        
                        # Recalculate speech timestamps with the new buffer
                        speech_timestamps = get_speech_timestamps(
                            waveform, 
                            vad_model, 
                            sampling_rate=SAMPLE_RATE,
                            min_speech_duration_ms=250,
                            max_speech_duration_s=float('inf'),
                            min_silence_duration_ms=1000,
                            speech_pad_ms=500,
                            threshold=0.3
                        )

                        # Extract first detected speech segment (or loop over all)
                        for seg in speech_timestamps:
                            start, end = seg['start'], seg['end']
                            speech_segment = waveform[:, start:end]

                            # Convert to bytes for speech_recognition
                            speech_np = (speech_segment.numpy().T *
                                         32768).astype(np.int16)
                            # 2 bytes per sample (int16)
                            audio_data = sr.AudioData(
                                speech_np.tobytes(), SAMPLE_RATE, 2)

                            try:
                                user_input = r.recognize_google(audio_data).lower()
                                
                                # Update the last speech time
                                last_speech_time = time.time()

                                if user_input in ["quit", "exit", "q"]:
                                    exit_event.set()
                                    print("Exit command detected. Stopping listener.")
                                    break

                                # Your existing processing here:
                                stream_graph_updates(user_input)

                            except sr.UnknownValueError:
                                # Only say "didn't catch that" if the energy level is high enough
                                # This prevents responding to background noise
                                segment_energy = torch.mean(torch.abs(speech_segment)).item()
                                if segment_energy > 0.03:  # Adjust this threshold as needed
                                    speakText("Sorry, I didn't catch that.")
                                    last_speech_time = time.time()
                            except sr.RequestError:
                                speakText("Speech recognition failed.")
                                last_speech_time = time.time()
                            except Exception:
                                speakText("An error occurred.")
                                last_speech_time = time.time()
                                exit_event.set()
                                break

                        # Remove processed audio from buffer
                        if speech_timestamps:
                            buffer = buffer[speech_timestamps[-1]['end']:]
                    else:
                        # If speech probability is too low, just trim the buffer
                        # but don't process it or respond
                        if speech_timestamps:
                            buffer = buffer[speech_timestamps[-1]['end']:]
                else:
                    # If no speech detected, keep buffer under control (avoid infinite growth)
                    max_buffer_len = SAMPLE_RATE * 5  # max 5 seconds buffer
                    if buffer.shape[0] > max_buffer_len:
                        buffer = buffer[-max_buffer_len:]

            except Empty:
                # No audio data received, continue waiting
                continue
            except KeyboardInterrupt:
                print("Interrupted by user.")
                exit_event.set()
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