import numpy as np
import parselmouth
import pyaudio
import json
import time
import threading

chunk = 1024
format = pyaudio.paInt16
channels = 1
rate = 44100
JSON_Filename = "_static/global/audio_analysis.json"

p = pyaudio.PyAudio()

stream = p.open(format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk)

frames = []

def calculate_pitch(sound):
    pitch = sound.to_pitch_ac(time_step=0.01, pitch_floor=75, pitch_ceiling=500)
    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]

    if len(pitch_values) > 0:
        mean_pitch = np.mean(pitch_values)
        std_pitch = np.std(pitch_values)
        filtered_pitch_values = pitch_values[np.abs(pitch_values - mean_pitch) < 3 * std_pitch]
        mean_pitch = np.mean(filtered_pitch_values)
        std_pitch = np.std(filtered_pitch_values)
    else:
        mean_pitch = 0
        std_pitch = 0

    return mean_pitch, std_pitch

def calculate_hnr(sound):
    harmonicity = sound.to_harmonicity_cc(time_step=0.01, minimum_pitch=75)
    hnr_values = harmonicity.values[harmonicity.values != -200]
    hnr = np.mean(hnr_values) if len(hnr_values) > 0 else 0
    return hnr

def calculate_zcr(audio_data):
    zero_crossings = np.where(np.diff(np.signbit(audio_data)))[0]
    zcr = len(zero_crossings) / len(audio_data)
    return zcr

def analyze_audio(audio_data, sample_rate):
    sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)

    mean_pitch, std_pitch = calculate_pitch(sound)
    hnr = calculate_hnr(sound)
    zcr = calculate_zcr(audio_data)

    return mean_pitch, std_pitch, hnr, zcr

def record_audio():
    global frames
    print("Recording started.")
    while True:
        data = stream.read(chunk)
        frames.append(data)

def analyze_audio_live():
    while True:
        if len(frames) > 0:
            audio_data = np.frombuffer(b''.join(frames[-int(rate / chunk * 5):]), dtype=np.int16)

            mean_pitch, std_pitch, hnr, zcr = analyze_audio(audio_data, rate)

            analysis_results = {
                "mean_pitch": mean_pitch,
                "std_pitch": std_pitch,
                "hnr": hnr,
                "zcr": zcr,
                "timestamp": time.time()
            }

            with open(JSON_Filename, 'w') as json_file:
                json.dump(analysis_results, json_file)

            print(f"Analysis results updated at {time.time()}")

        time.sleep(5)

recording_thread = threading.Thread(target=record_audio)
analysis_thread = threading.Thread(target=analyze_audio_live)

recording_thread.start()
analysis_thread.start()
