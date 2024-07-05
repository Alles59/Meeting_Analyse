import pyaudio
import numpy as np
import time

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_DURATION = 5  # 5 seconds
CHUNK = int(RATE * BUFFER_DURATION)

audio = pyaudio.PyAudio()

# Function to get the index of the device by name
def get_device_index(device_name):
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if device_name.lower() in info['name'].lower():
            return i
    raise Exception(f"Device '{device_name}' not found")

# Print all available devices
def print_all_devices():
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']}")

print_all_devices()

# Find the indices for Stereo Mix and Microphone
STEREO_MIX_INDEX = get_device_index("Stereomix")
MICROPHONE_INDEX = get_device_index("Mikrofon")

def capture_audio():
    stereo_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=STEREO_MIX_INDEX, frames_per_buffer=CHUNK)
    mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=MICROPHONE_INDEX, frames_per_buffer=CHUNK)

    try:
        while True:
            stereo_data = np.frombuffer(stereo_stream.read(CHUNK), dtype=np.int16)
            mic_data = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
            combined_data = (stereo_data + mic_data) // 2
            np.save("_static/global/audio_buffer.npy", combined_data)
            print(f"Saved audio buffer of {BUFFER_DURATION} seconds.")
            time.sleep(BUFFER_DURATION)
    except KeyboardInterrupt:
        print("Audio capture stopped.")
    finally:
        stereo_stream.stop_stream()
        stereo_stream.close()
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

if __name__ == "__main__":
    capture_audio()
