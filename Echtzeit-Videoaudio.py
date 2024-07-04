import numpy as np
import parselmouth
import moviepy.editor as mp
import tempfile
import os
import json
import sys

def calculate_pitch(sound):
    pitch = sound.to_pitch_ac(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
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

def detect_gender(mean_pitch):
    if mean_pitch > 165:
        return "female"
    else:
        return "male"

def process_video(video_path):
    video = mp.VideoFileClip(video_path)
    audio = video.audio

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
        audio.write_audiofile(temp_wav_file.name, fps=44100)
        temp_wav_path = temp_wav_file.name

    sound = parselmouth.Sound(temp_wav_path)
    os.remove(temp_wav_path)
    return sound, video.duration

def main(video_path, output_path):
    sound, duration = process_video(video_path)
    interval = 5
    timestamps = np.arange(0, duration, interval)
    analysis_results = {}

    for timestamp in timestamps:
        start_time = timestamp
        end_time = timestamp + interval
        sub_sound = sound.extract_part(from_time=start_time, to_time=end_time, preserve_times=True)
        
        mean_pitch, std_pitch, hnr, zcr = analyze_audio(sub_sound.values[0], sub_sound.sampling_frequency)
        gender = detect_gender(mean_pitch)

        analysis_results[int(timestamp)] = {
            "mean_pitch": mean_pitch,
            "std_pitch": std_pitch,
            "hnr": hnr,
            "zcr": zcr,
            "gender": gender
        }

    with open(output_path, 'w') as outfile:
        json.dump(analysis_results, outfile, indent=4)

    print(f"Audioanalyse abgeschlossen. JSON gespeichert unter {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Verwendung: python Echtzeit-Videoaudio.py <path_to_video> <path_to_output_json>")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = "_static/global/audio_analysis.json"
    main(video_path, output_path)
