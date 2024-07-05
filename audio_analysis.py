import numpy as np
import parselmouth
import os
import json
import time

def calculate_pitch(sound):
    pitch = sound.to_pitch_ac()
    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]
    mean_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0
    std_pitch = np.std(pitch_values) if len(pitch_values) > 0 else 0
    return mean_pitch, std_pitch

def calculate_hnr(sound):
    harmonicity = sound.to_harmonicity()
    hnr_values = harmonicity.values[harmonicity.values != -200]
    hnr = np.mean(hnr_values) if len(hnr_values) > 0 else 0
    return hnr

def calculate_zcr(audio_data):
    zero_crossings = np.where(np.diff(np.signbit(audio_data)))[0]
    zcr = len(zero_crossings) / len(audio_data)
    return zcr

def detect_gender(mean_pitch):
    if mean_pitch < 165:
        return "male"
    else:
        return "female"

def analyze_audio():
    while True:
        if os.path.exists("_static/global/audio_buffer.npy"):
            current_buffer = np.load("_static/global/audio_buffer.npy")
            sound = parselmouth.Sound(current_buffer, 44100)
            mean_pitch, std_pitch = calculate_pitch(sound)
            hnr = calculate_hnr(sound)
            zcr = calculate_zcr(current_buffer)
            gender = detect_gender(mean_pitch)

            result = {
                "mean_pitch": mean_pitch,
                "std_pitch": std_pitch,
                "hnr": hnr,
                "zcr": zcr,
                "gender": gender
            }
            with open("_static/global/audio_analysis.json", "w") as f:
                json.dump(result, f, indent=4)
            print("Audio analysis complete, JSON updated.")

        time.sleep(5)

if __name__ == "__main__":
    analyze_audio()
