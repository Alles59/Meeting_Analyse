# Importiert notwendige Bibliotheken
import cv2  # OpenCV für die Videobearbeitung
from deepface import DeepFace  # DeepFace für die Emotionserkennung
import numpy as np  # NumPy für numerische Operationen
import os  # OS-Bibliothek für Dateioperationen
import pandas as pd  # Pandas für die Datenmanipulation und -speicherung

def analyze_video_emotions(video_path, interval=1, frame_skip=30, model_name='Facenet512'):
    # Überprüft, ob die Videodatei existiert
    if not os.path.exists(video_path):
        print(f"Fehler: Videodatei {video_path} existiert nicht.")
        return []

    # Lädt das angegebene Modell (hier Facenet512)
    model = DeepFace.build_model(model_name)

    # Lädt das Video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Fehler: Konnte das Video nicht öffnen.")
        return []

    # Ermittelt die Bildrate des Videos
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    # Berechnet die Anzahl der Frames pro Intervall
    interval_frames = int(interval * frame_rate)
    # Initialisiert eine Liste, um die durchschnittlichen Emotionen pro Intervall zu speichern
    emotions_per_interval = []

    # Initialisiert den Frame-Zähler und eine Liste, um die Emotionen zu speichern
    frame_count = 0
    emotions = []

    # Durchläuft jedes Frame im Video
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Beendet die Schleife, wenn keine Frames mehr vorhanden sind

        # Verarbeitet jedes n-te Frame basierend auf frame_skip
        if frame_count % frame_skip == 0:
            try:
                # Analysiert die Emotionen im aktuellen Frame mit dem angegebenen Modell
                obj = DeepFace.analyze(img_path=frame, actions=['emotion'], enforce_detection=True, detector_backend='opencv')
                # Fügt die erkannten Emotionen der Liste hinzu
                emotions.append(list(obj[0]['emotion'].values()))
                print(f"Frame {frame_count}: Erkannte Emotionen {obj[0]['emotion']}")
            except Exception as e:
                # Behandelt Fälle, in denen kein Gesicht erkannt wird oder andere Fehler auftreten
                print(f"Frame {frame_count}: Kein Gesicht erkannt oder anderer Fehler: {e}")
                pass

        # Berechnet die durchschnittlichen Emotionen am Ende jedes Intervalls
        if frame_count % interval_frames == 0 and frame_count != 0:
            if emotions:
                avg_emotions = np.mean(emotions, axis=0)
                emotions_per_interval.append(avg_emotions)
                print(f"Verarbeitetes Intervall {len(emotions_per_interval)} mit durchschnittlichen Emotionen: {avg_emotions}")
            # Setzt die Emotionsliste für das nächste Intervall zurück
            emotions = []

        frame_count += 1

    # Behandelt das letzte Intervall, wenn noch Emotionen übrig sind
    if emotions:
        avg_emotions = np.mean(emotions, axis=0)
        emotions_per_interval.append(avg_emotions)
        print(f"Verarbeitetes Intervall {len(emotions_per_interval)} mit durchschnittlichen Emotionen: {avg_emotions}")

    # Gibt das Video-Capture-Objekt frei
    cap.release()
    return emotions_per_interval

def save_emotions_to_excel(emotions_per_interval, output_path):
    # Definiert die Emotionslabel
    emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    # Bereitet die Daten für das DataFrame vor
    data = []
    for idx, emotions in enumerate(emotions_per_interval):
        # Bestimmt die dominante Emotion für das Intervall
        max_emotion = emotion_labels[np.argmax(emotions)]
        data.append([idx + 1] + list(emotions) + [max_emotion])
    # Erstellt ein DataFrame mit den Emotionsdaten und der dominanten Emotion
    df = pd.DataFrame(data, columns=['Intervall (s)'] + emotion_labels + ['Dominante Emotion'])
    # Speichert das DataFrame in einer Excel-Datei
    df.to_excel(output_path, index=False)
    print(f"Ergebnisse gespeichert in {output_path}")

# Pfade zur Videodatei und zur Ausgabe-Excel-Datei
video_path = "C:/Users/.../.../.../.mp4"
output_path = "C:/Users/.../.../.../.xlsx"

# Analysiert die Emotionen im Video mit dem Modell Facenet512 und speichert die Ergebnisse in Excel
emotions_per_interval = analyze_video_emotions(video_path, interval=1, frame_skip=30, model_name='Facenet512')
save_emotions_to_excel(emotions_per_interval, output_path)
