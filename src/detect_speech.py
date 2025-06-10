import torch
import sounddevice as sd
import numpy as np
import speech_recognition as sr
from queue import Queue, Empty
import threading

# Globals
r = sr.Recognizer()
exit_event = threading.Event()

# Load Silero VAD model once
vad_model, get_speech_timestamps = torch.hub.load('snakers4/silero-vad', 'silero_vad', force_reload=False)[0:2]

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5  # seconds per audio chunk to process

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
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=audio_callback):
        buffer = np.zeros((0, CHANNELS), dtype='int16')
        
        while not exit_event.is_set():
            try:
                # Collect audio chunks from queue
                data = q.get(timeout=1)  # wait for max 1 sec
                
                # Append new data to buffer
                buffer = np.concatenate((buffer, data), axis=0)
                
                # Convert buffer to torch tensor and normalize to float32 (-1.0 to 1.0)
                waveform = torch.from_numpy(buffer.T.astype(np.float32) / 32768.0)
                
                # Run VAD on the buffered audio
                speech_timestamps = get_speech_timestamps(waveform, vad_model, sampling_rate=SAMPLE_RATE)
                
                if speech_timestamps:
                    # Extract first detected speech segment (or loop over all)
                    for seg in speech_timestamps:
                        start, end = seg['start'], seg['end']
                        speech_segment = waveform[:, start:end]
                        
                        # Convert to bytes for speech_recognition
                        speech_np = (speech_segment.numpy().T * 32768).astype(np.int16)
                        audio_data = sr.AudioData(speech_np.tobytes(), SAMPLE_RATE, 2)  # 2 bytes per sample (int16)
                        
                        try:
                            user_input = r.recognize_google(audio_data).lower()
                            print(f"You said: {user_input}")
                            
                            if user_input in ["quit", "exit", "q"]:
                                exit_event.set()
                                print("Exit command detected. Stopping listener.")
                                break
                            
                            # Your existing processing here:
                            stream_graph_updates(user_input)
                            
                        except sr.UnknownValueError:
                            speakText("Sorry, I didn't catch that.")
                        except sr.RequestError:
                            speakText("Speech recognition failed.")
                        except Exception as e:
                            speakText("An error occurred.")
                            exit_event.set()
                            break
                    
                    # Remove processed audio from buffer
                    buffer = buffer[end:]
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
