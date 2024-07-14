import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import iqr
from pydub import AudioSegment


def calculate_decibels_for_intervals(audio_path, interval_length=1):
    """
    Berechnet die Dezibelwerte für festgelegte Intervalle einer Audiodatei.

    :param audio_path: Pfad zur Audiodatei.
    :param interval_length: Länge des Intervalls in Sekunden.
    :return: Array der Dezibelwerte.
    """
    # Lade die Audiodatei
    audio = AudioSegment.from_file(audio_path)

    # Konvertiere AudioSegment zu numpy-Array
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Berechne Dezibelwerte für jedes Intervall
    interval_samples = int(interval_length * audio.frame_rate)
    decibels = []
    for i in range(0, len(samples), interval_samples):
        interval = samples[i:i + interval_samples]
        if len(interval) > 0:
            rms = np.sqrt(np.mean(interval ** 2))
            db = 20 * np.log10(rms + 1e-6)
            decibels.append(db)
    return np.array(decibels)


def calculate_tempo_for_intervals(y, sr, interval_length=1):
    """
    Berechnet das Tempo (BPM) für festgelegte Intervalle einer Audiodatei.

    :param y: Audiosignal.
    :param sr: Sampling-Rate des Audiosignals.
    :param interval_length: Länge des Intervalls in Sekunden.
    :return: Array der BPM-Werte.
    """
    hop_length = 512
    interval_samples = int(interval_length * sr)
    tempos = []
    for i in range(0, len(y), interval_samples):
        interval = y[i:i + interval_samples]
        if len(interval) > 0:
            onset_env = librosa.onset.onset_strength(y=interval, sr=sr, hop_length=hop_length)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            tempos.append(tempo)
    return np.array(tempos)


def extract_features(file_path, interval_length=1):
    """
    Extrahiert verschiedene Audio-Features aus einer Audiodatei.

    :param file_path: Pfad zur Audiodatei.
    :param interval_length: Länge der Intervalle in Sekunden.
    :return: Tuple aus DataFrame der Rohdaten, DataFrame der durchschnittlichen Werte pro Sekunde,
             durchschnittliches Tempo, Pitch-Standardabweichung und Peak-Slopes.
    """
    # Laden der Audio-Datei
    y, sr = librosa.load(file_path)

    # Pitch-Schätzung mit der PYIN-Methode
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))

    # Zeitachse berechnen
    times = librosa.times_like(f0, sr=sr)

    # Berechnung der Dezibelwerte für Intervalle
    rms_db_intervals = calculate_decibels_for_intervals(file_path, interval_length)
    rms_db_times = np.linspace(0, len(y) / sr, len(rms_db_intervals))
    rms_db = np.interp(times, rms_db_times, rms_db_intervals)

    # Berechnung der BPM-Werte für Intervalle
    tempo_intervals = calculate_tempo_for_intervals(y, sr, interval_length)
    tempo_times = np.linspace(0, len(y) / sr, len(tempo_intervals))
    tempo_bpm = np.interp(times, tempo_times, tempo_intervals.flatten())

    # Zero Crossing Rate (Aussprache)
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    # MFCCs (Betonung)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfccs, axis=1)

    # Standardabweichung der Pitch (Sprachmelodie)
    pitch_std = np.nanstd(f0)

    # Berechnung der Peak Slopes
    peaks = librosa.util.peak_pick(f0, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.5, wait=5)
    peak_times = times[peaks]
    peak_slopes = np.diff(f0[peaks]) / np.diff(peak_times) if len(peaks) > 1 else np.array([])

    # Berechnung der durchschnittlichen Werte pro Sekunde
    data = {
        'Time': times,
        'Pitch': f0,
        'RMS_dB': rms_db,
        'ZCR': np.interp(times, np.linspace(0, len(y) / sr, len(zcr)), zcr),
        'MFCC_Mean': np.mean(mfccs, axis=0),
        'Tempo_BPM': tempo_bpm
    }

    df = pd.DataFrame(data)
    df['Time_sec'] = df['Time'].astype(int)

    def remove_outliers(series):
        """
        Entfernt Ausreißer aus einer Serie basierend auf dem IQR.
        
        :param series: Eingabewerte.
        :return: Serie ohne Ausreißer.
        """
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr_value = q3 - q1
        lower_bound = q1 - 1.5 * iqr_value
        upper_bound = q3 + 1.5 * iqr_value
        return series[(series >= lower_bound) & (series <= upper_bound)]

    df_avg = df.groupby('Time_sec').agg({
        'Pitch': lambda x: remove_outliers(x).mean(),
        'RMS_dB': lambda x: remove_outliers(x).mean(),
        'ZCR': lambda x: remove_outliers(x).mean(),
        'MFCC_Mean': lambda x: remove_outliers(x).mean(),
        'Tempo_BPM': lambda x: remove_outliers(x).mean()
    }).reset_index()

    # Hinzufügen der Standardabweichung des Pitches als Spalte
    df_avg['Pitch_Std'] = df.groupby('Time_sec')['Pitch'].std().reset_index(drop=True)

    return df, df_avg, np.mean(tempo_intervals), pitch_std, peak_slopes


# Dateiauswahl
file_path = 'Tief.wav'  # Pfad zur WAV- oder MP3-Datei
df, df_avg, tempo_bpm, pitch_std, peak_slopes = extract_features(file_path)

# Speichern der Rohdaten und der durchschnittlichen Werte pro Sekunde in CSV-Dateien
df.to_csv('extracted_features_raw.csv', index=False)
df_avg.to_csv('extracted_features_avg_per_sec.csv', index=False)

print(f"Die Merkmale wurden in 'extracted_features_raw.csv' und 'extracted_features_avg_per_sec.csv' gespeichert.")
print(f"Durchschnittliches Tempo: {tempo_bpm} BPM")
print(f"Pitch Standardabweichung: {pitch_std} Hz")
print(f"Peak Slopes: {peak_slopes}")

# Optional: Plotten der extrahierten Pitches
plt.plot(df['Time'], df['Pitch'], label='Pitch (F0)')
plt.title('Extracted Pitch')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.legend()
plt.show()
