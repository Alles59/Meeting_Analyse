import parselmouth
from parselmouth.praat import call
import numpy as np

# Lade die Audiodatei
audio_path = "Meeting_Analyse\2024-06-28 00-43-35.wav"
sound = parselmouth.Sound(audio_path)

# Bestimme die Grundfrequenz (f0) mit der 'filtered autocorrelation' Methode
pitch = sound.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=800)

# Extrahiere die Pitch Werte und Zeitwerte
pitch_values = pitch.selected_array['frequency']
time_values = pitch.xs()

# Funktion, um die Mittelwerte der Grundfrequenz in 5-Sekunden-Intervallen zu berechnen
def mean_pitch_intervals(pitch, interval=5.0):
    duration = pitch.xmax - pitch.xmin
    intervals = int(np.ceil(duration / interval))
    mean_pitches = []

    for i in range(intervals):
        start_time = i * interval
        end_time = start_time + interval
        mean_pitch = call(pitch, "Get mean", start_time, end_time, "Hertz")
        mean_pitches.append((start_time, end_time, mean_pitch))
    
    return mean_pitches

# Berechnung der Mittelwerte der Grundfrequenz
mean_pitches = mean_pitch_intervals(pitch)

# Ausgabe der Mittelwerte der Grundfrequenz in 5-Sekunden-Intervallen
for start, end, mean_pitch in mean_pitches:
    print(f"Interval: {start:.1f} s - {end:.1f} s, Mean Pitch: {mean_pitch:.2f} Hz")
