import numpy as np
import parselmouth
import json
from moviepy.editor import VideoFileClip
import os
import time
import tempfile
from scipy.io import wavfile

def calculate_pitch(sound):
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=50, pitch_ceiling=500)
    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]  # Remove unvoiced parts

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
    harmonicity = sound.to_harmonicity_cc(time_step=0.01, minimum_pitch=50)
    hnr_values = harmonicity.values[harmonicity.values != -200]  # Filter out invalid values
    hnr = np.mean(hnr_values) if len(hnr_values) > 0 else 0
    return hnr

def calculate_zcr(audio_data):
    zero_crossings = np.where(np.diff(np.signbit(audio_data)))[0]
    zcr = len(zero_crossings) / len(audio_data)
    return zcr

def calculate_intensity(sound):
    intensity = sound.to_intensity(time_step=0.01)
    intensity_values = intensity.values.T
    mean_intensity = np.mean(intensity_values) if intensity_values.size > 0 else 0

    ref_pressure = 20e-6  # Referenzschalldruck in Pascal
    mean_intensity_spl = 20 * np.log10(mean_intensity / ref_pressure) if mean_intensity > 0 else 0

    return mean_intensity_spl

def analyze_audio(audio_data, sample_rate):
    sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)
    print(f"Sample rate: {sample_rate}")
    print(f"Audio duration: {sound.get_total_duration()} seconds")

    if sound.get_total_duration() < 0.1:  # Ensure there is enough audio data for analysis
        raise ValueError("Audio data is too short for analysis")

    mean_pitch, std_pitch = calculate_pitch(sound)
    hnr = calculate_hnr(sound)
    zcr = calculate_zcr(audio_data)
    mean_intensity_spl = calculate_intensity(sound)

    results = {
        "mean_pitch": mean_pitch,
        "std_pitch": std_pitch,
        "hnr": hnr,
        "zcr": zcr,
        "mean_intensity_spl": mean_intensity_spl,
    }

    with open('Meeting_Analyse/audio_analysis.json', 'w') as json_file:
        json.dump(results, json_file)

    return results

def extract_audio_from_video(video_file):
    clip = VideoFileClip(video_file)
    audio = clip.audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        temp_wav_path = temp_wav.name
        audio.write_audiofile(temp_wav_path, fps=44100)
    sample_rate, audio_data = wavfile.read(temp_wav_path)
    os.remove(temp_wav_path)
    return audio_data, sample_rate

def main():
    video_file = os.getenv('VIDEO_PATH')
    if not video_file:
        print("No video file path provided.")
        return

    while True:
        if os.path.exists(video_file):
            audio_data, sample_rate = extract_audio_from_video(video_file)
            results = analyze_audio(audio_data, sample_rate)
            print(results)
        else:
            print(f"Waiting for video file {video_file} to appear...")
        time.sleep(5)  # Wait for 5 seconds

if __name__ == "__main__":
    main()
