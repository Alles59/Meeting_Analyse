import pyaudio
import numpy as np
import parselmouth
import wave
import json
import threading
import time
import signal
import sys

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILENAME = "_static/global/Recorded.wav"
JSON_FILENAME = "_static/global/audio_analysis.json"
RECORD_SECONDS = 5  # Save and analyze every 5 seconds

p = pyaudio.PyAudio()

# Indices of the desired devices
mic_index = 1  # Set your microphone device index here
stereo_index = 2  # Set your stereo mix device index here

# Streams
mic_stream = None
stereo_stream = None
recording = False
stop_event = threading.Event()

def list_audio_devices():
    device_count = p.get_device_count()
    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']}")

def start_recording():
    global mic_stream, stereo_stream, recording
    recording = True
    
    mic_stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=mic_index,
                        frames_per_buffer=CHUNK)

    stereo_stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           input_device_index=stereo_index,
                           frames_per_buffer=CHUNK)

    frames = []
    while recording and not stop_event.is_set():
        mic_data = mic_stream.read(CHUNK)
        stereo_data = stereo_stream.read(CHUNK)

        # Convert byte data to numpy arrays
        mic_array = np.frombuffer(mic_data, dtype=np.int16)
        stereo_array = np.frombuffer(stereo_data, dtype=np.int16)

        # Combine the two audio sources
        combined_array = mic_array + stereo_array

        # Normalize the combined array to prevent clipping
        combined_array = normalize_audio(combined_array)

        # Convert combined array back to byte data
        combined_data = combined_array.tobytes()
        
        frames.append(combined_data)
        if len(frames) >= int(RATE / CHUNK * RECORD_SECONDS):  # Save and analyze every 5 seconds
            save_and_analyze(frames)
            frames = []
            time.sleep(0.5)  # Add a short delay to ensure processing catches up
    stop_recording()

def stop_recording():
    global mic_stream, stereo_stream, recording
    recording = False
    if mic_stream:
        mic_stream.stop_stream()
        mic_stream.close()
    if stereo_stream:
        stereo_stream.stop_stream()
        stereo_stream.close()
    p.terminate()
    stop_event.set()

def save_and_analyze(frames):
    # Save frames as WAV file
    wf = wave.open(OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Analyze audio with Parselmouth
    audio_buffer = b''.join(frames)
    audio_np = np.frombuffer(audio_buffer, dtype=np.int16)
    
    # Analyze audio
    mean_pitch, std_pitch, hnr, zcr = analyze_audio(audio_np, RATE)
    gender = detect_gender(mean_pitch)
    
    analysis_data = {
        'mean_pitch': mean_pitch,
        'std_pitch': std_pitch,
        'hnr': hnr,
        'zcr': zcr,
        'gender': gender
    }
    
    with open(JSON_FILENAME, 'w') as f:
        json.dump(analysis_data, f)
    
    print("Audio analysis complete, JSON updated.")

def normalize_audio(audio_data):
    max_val = np.iinfo(np.int16).max
    audio_data = audio_data * (max_val / np.max(np.abs(audio_data)))
    return audio_data.astype(np.int16)

def calculate_pitch(sound):
    pitch = sound.to_pitch_ac(pitch_floor=50, max_number_of_candidates= 15, very_accurate = False, silence_threshold=0.09, voicing_threshold= 0.50, octave_cost= 0.055, octave_jump_cost = 0.35, voiced_unvoiced_cost = 0.14, pitch_ceiling=500)
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

def handle_signal(signal, frame):
    print('Stopping recording...')
    stop_recording()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# List devices to allow user to select the correct one
list_audio_devices()

# Example usage:
# recording_thread = threading.Thread(target=start_recording)
# recording_thread.daemon = True
# recording_thread.start()
# time.sleep(10)
# stop_recording()
