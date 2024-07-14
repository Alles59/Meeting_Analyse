import pyaudio
import wave

def record_audio(filename, duration, sample_rate=44100, channels=2, chunk_size=1024):
    # Initialisierung des PyAudio Objekts
    audio = pyaudio.PyAudio()

    # Audio-Stream konfigurieren
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)

    print("Aufnahme gestartet...")

    # Liste zum Speichern der Audio-Frames
    frames = []

    # Aufnahme-Schleife
    for i in range(0, int(sample_rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(data)

    print("Aufnahme beendet.")

    # Beenden des Streams und Schließen des PyAudio Objekts
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Speichern der Aufnahme als WAV-Datei
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

# Beispiel für die Verwendung:
# Aufnahme einer 5 Sekunden langen Audio-Datei namens "aufnahme.wav"
record_audio("aufnahme.wav", duration=5)
