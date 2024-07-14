import logging  # Importiert das Logging-Modul zur Protokollierung
import threading  # Importiert das threading-Modul zur Erstellung von Threads
import queue  # Importiert das queue-Modul für Thread-Kommunikation
import json  # Importiert das json-Modul zum Arbeiten mit JSON-Daten
import time  # Importiert das time-Modul für Zeitfunktionen
import os  # Importiert das os-Modul für Betriebssystemfunktionen
import io  # Importiert das io-Modul für Ein-/Ausgabe-Operationen
from datetime import datetime, timedelta  # Importiert datetime-Module für Datums- und Zeitoperationen
import signal  # Importiert das signal-Modul zur Signalbehandlung

import cv2  # Importiert OpenCV für Bildverarbeitung
import numpy as np  # Importiert NumPy für numerische Operationen
import pandas as pd  # Importiert Pandas für Datenanalyse
import matplotlib.pyplot as plt  # Importiert Matplotlib für Diagramme
import mss  # Importiert mss für Bildschirmaufnahmen
from deepface import DeepFace  # Importiert DeepFace für Gesichtserkennung und Emotionserkennung
from flask import Flask, jsonify, request, Response  # Importiert Flask für Webserver
from flask_cors import CORS  # Importiert Flask-CORS zur Handhabung von Cross-Origin Resource Sharing
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas  # Importiert FigureCanvas für die Erstellung von Diagrammen
import tkinter as tk  # Importiert tkinter für GUI-Interaktionen
from tkinter import simpledialog  # Importiert simpledialog für einfache Dialoge in tkinter

# Initialisiert die Flask-App
app = Flask(__name__)
CORS(app)  # Aktiviert CORS für die Flask-App

# Setzt das Backend für Matplotlib auf Agg
plt.switch_backend('Agg')

# Konfiguriert das Logging
logging.basicConfig(level=logging.INFO)

# Globale Variablen zur Speicherung mehrerer ROIs und ihrer Namen
rois = []
roi_names = []
results = []
analysis_thread = None
stop_event = threading.Event()
results_file = 'results.json'
rois_file = 'rois.json'  # Neue Datei zur Speicherung der ROIs
tkinter_queue = queue.Queue()

# Intervall in Sekunden, in dem Screenshots gemacht werden
SCREENSHOT_INTERVAL = 1
# Intervall in Sekunden, in dem die Durchschnittswerte berechnet und in den Balkendiagrammen angezeigt werden
AVERAGE_INTERVAL = 5

# Farben für verschiedene Emotionen
emotion_colors = {
    'angry': 'red',
    'fear': 'purple',
    'happy': 'yellow',
    'neutral': 'black',
    'disgust': 'green',
    'sad': 'blue',
    'surprise': 'pink'
}

def signal_handler(sig, frame):
    """Signalhandler zur Behandlung von Programmbeendigungen"""
    stop_event.set()  # Setzt das Stop-Event
    tkinter_queue.put(None)  # Beendet den tkinter-Thread
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)  # Verknüpft SIGINT mit dem Signalhandler

def save_rois():
    """Speichert die ROIs in einer JSON-Datei"""
    global rois, roi_names
    with open(rois_file, 'w') as f:
        json.dump({'rois': rois, 'roi_names': roi_names}, f)

def load_rois():
    """Lädt die ROIs aus einer JSON-Datei"""
    global rois, roi_names
    try:
        with open(rois_file, 'r') as f:
            data = json.load(f)
            rois = data['rois']
            roi_names = data['roi_names']
            # Filtert leere oder ungültige ROI-Namen heraus
            rois, roi_names = zip(*[(roi, name) for roi, name in zip(rois, roi_names) if name])
            rois = list(rois)
            roi_names = list(roi_names)
            logging.debug(f"Loaded ROIs: {rois}")
            logging.debug(f"Loaded ROI names: {roi_names}")
    except (FileNotFoundError, json.JSONDecodeError):
        rois = []
        roi_names = []
        logging.debug("No ROIs found or error in loading.")
    clear_results()  # Alte Analyseergebnisse löschen
    logging.debug(f"ROIs after clearing results: {rois}")
    logging.debug(f"ROI names after clearing results: {roi_names}")
    return jsonify(status="ROIs geladen und alte Ergebnisse gelöscht.", rois=rois, roi_names=roi_names)

def clear_results():
    """Löscht die Analyseergebnisse"""
    global results
    results = []
    with open(results_file, 'w') as f:
        json.dump(results, f)
    logging.debug("Analysis results cleared.")

@app.route('/select_rois', methods=['POST'])
def select_rois():
    """Wählt ROIs aus und speichert sie"""
    global rois, roi_names
    rois = []
    roi_names = []
    clear_results()  # Ergebnisse leeren
    tkinter_queue.put(select_rois_logic)
    tkinter_queue.join()  # Warten, bis der Tkinter-Aufruf abgeschlossen ist
    save_rois()  # ROIs speichern
    return jsonify(status="ROIs ausgewählt.")

@app.route('/load_rois', methods=['POST'])
def load_saved_rois():
    """Lädt gespeicherte ROIs und löscht alte Ergebnisse"""
    load_rois()
    clear_results()  # Alte Analyseergebnisse löschen
    return jsonify(status="ROIs loaded and old results deleted", rois=rois, roi_names=roi_names)

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Startet die Analyse der Emotionen auf dem Bildschirm"""
    global analysis_thread, stop_event
    stop_event.clear()
    if analysis_thread is None or not analysis_thread.is_alive():
        analysis_thread = threading.Thread(target=analyze_screen_emotions)
        analysis_thread.start()
    return jsonify(status="Analysis started")

@app.route('/stop_analysis', methods=['POST'])
def stop_analysis():
    """Stoppt die laufende Analyse"""
    global stop_event
    stop_event.set()
    return jsonify(status="Analysis stopped")

@app.route('/bar_chart.png', methods=['GET'])
def bar_chart_png():
    """Erzeugt ein Balkendiagramm der Emotionsergebnisse"""
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = []

    df = pd.DataFrame(results, columns=['Timestamp', 'Roi', 'Emotion', 'Emotions'])

    if len(roi_names) > 0:
        fig, axes = plt.subplots(len(roi_names) + 1, 1, figsize=(10, 5 * (len(roi_names) + 1)))
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        time_threshold = datetime.now() - timedelta(seconds=AVERAGE_INTERVAL)
        filtered_df = df[df['Timestamp'] >= time_threshold]

        # Kumulatives Diagramm für alle ROIs
        emotions_df = filtered_df['Emotions'].apply(pd.Series)
        if isinstance(emotions_df, pd.DataFrame):
            emotion_means = emotions_df.mean()
            emotion_counts = emotion_means.reindex(emotion_colors.keys(), fill_value=0)
            if emotion_counts.sum() > 0:  # Überprüfen, ob es nicht null Ergebnisse gibt
                axes[0].bar(emotion_counts.index, emotion_counts.values, color=[emotion_colors[emotion] for emotion in emotion_counts.index])
                axes[0].set_ylabel('Frequency (%)')
                axes[0].set_title(f'Average Emotion Distribution Over Time ({AVERAGE_INTERVAL} seconds) - All ROIs', fontsize=14, fontweight='bold')
                axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
                axes[0].set_ylim(0, 100)  # Y-Achse auf 100% skalieren
                axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)
            else:
                axes[0].remove()  # Kumulatives Subplot entfernen, wenn keine Daten vorhanden sind
        else:
            axes[0].remove()  # Kumulatives Subplot entfernen, wenn keine Daten vorhanden sind

        for i, roi_name in enumerate(roi_names):
            roi_df = filtered_df[filtered_df['Roi'] == roi_name]
            if not roi_df.empty:
                roi_emotions_df = roi_df['Emotions'].apply(pd.Series)
                if isinstance(roi_emotions_df, pd.DataFrame):
                    roi_emotion_means = roi_emotions_df.mean()
                    roi_emotion_counts = roi_emotion_means.reindex(emotion_colors.keys(), fill_value=0)
                    if roi_emotion_counts.sum() > 0:  # Überprüfen, ob es nicht null Ergebnisse gibt
                        axes[i + 1].bar(roi_emotion_counts.index, roi_emotion_counts.values, color=[emotion_colors[emotion] for emotion in emotion_counts.index])
                        axes[i + 1].set_ylabel('Frequency (%)')
                        axes[i + 1].set_title(f'Average Emotion Distribution Over Time ({AVERAGE_INTERVAL} seconds) - ROI: {roi_name}', fontsize=14, fontweight='bold')
                        axes[i + 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
                        axes[i + 1].set_ylim(0, 100)  # Y-Achse auf 100% skalieren
                        axes[i + 1].grid(True, which='both', linestyle='--', linewidth=0.5)
                    else:
                        axes[i + 1].remove()  # Leeres Subplot entfernen
                else:
                    axes[i + 1].remove()  # Leeres Subplot entfernen
            else:
                axes[i + 1].remove()  # Leeres Subplot entfernen
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(emotion_colors.keys(), [0] * len(emotion_colors), color=[emotion_colors[emotion] for emotion in emotion_colors.keys()])
        ax.set_ylabel('Frequency (%)')
        ax.set_title(f'Average Emotion Distribution Over Time ({AVERAGE_INTERVAL} seconds) - All ROIs', fontsize=14, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
        ax.set_ylim(0, 100)  # Y-Achse auf 100% skalieren
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    canvas = FigureCanvas(fig)
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    png_output.seek(0)

    return Response(png_output.getvalue(), mimetype='image/png')


@app.route('/live_results', methods=['GET'])
def live_results():
    """Gibt die aktuellen Analyseergebnisse zurück"""
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        results = []

    latest_results = {}
    for result in results:
        timestamp, roi_name, dominant_emotion, _ = result
        latest_results[roi_name] = {
            'Timestamp': timestamp,
            'Roi': roi_name,
            'Dominant_Emotion': dominant_emotion
        }

    latest_results_list = list(latest_results.values())
    logging.info(f"Live results: {latest_results_list}")

    return jsonify(latest_results_list)

def save_results():
    """Speichert die Analyseergebnisse in einer JSON-Datei"""
    with open(results_file, 'w') as f:
        json.dump(results, f)

def select_rois_logic():
    """Logik zur Auswahl von ROIs"""
    global rois, roi_names, frame, ix, iy, drawing

    drawing = False
    ix, iy = -1, -1

    def draw_rectangle(event, x, y, flags, param):
        """Callback-Funktion zum Zeichnen eines Rechtecks"""
        global ix, iy, drawing
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                img = frame.copy()
                cv2.rectangle(img, (ix, iy), (x, y), (255, 0, 0), 2)
                cv2.imshow('Select ROIs', img)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            cv2.rectangle(frame, (ix, iy), (x, y), (255, 0, 0), 2)
            rois.append((ix, iy, x - ix, y - iy))
            ask_roi_name()
            cv2.imshow('Select ROIs', frame)

    # Verwendet MSS, um einen Screenshot zu machen
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        frame = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
        cv2.namedWindow('Select ROIs')
        cv2.setMouseCallback('Select ROIs', draw_rectangle)
        cv2.imshow('Select ROIs', frame)

        logging.info("Press 's' to start analysis after selecting all ROIs.")
        
        while True:
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

        cv2.destroyAllWindows()  # Fenster schließen, wenn 's' gedrückt wird

def ask_roi_name():
    """Fragt nach dem Namen eines ROI"""
    global roi_names
    root = tk.Tk()
    root.withdraw()
    roi_name = simpledialog.askstring("ROI Name", "Enter name for this ROI:")
    root.destroy()
    if roi_name:
        roi_names.append(roi_name)

def analyze_screen_emotions():
    """Analysiert die Emotionen auf dem Bildschirm in definierten Intervallen"""
    global rois, roi_names, results, stop_event

    if not rois:
        select_rois_logic()

    model = DeepFace.build_model('Facenet512')

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while not stop_event.is_set():
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            current_time = datetime.now()
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

            frame_results = []
            for roi, roi_name in zip(rois, roi_names):
                x, y, w, h = roi
                frame_roi = frame[y:y + h, x:x + w]
                try:
                    obj = DeepFace.analyze(img_path=frame_roi, actions=['emotion'], enforce_detection=True, detector_backend='opencv')
                    emotions = obj[0]['emotion']
                    dominant_emotion = max(emotions, key=emotions.get)
                    frame_results.append([current_time_str, roi_name, dominant_emotion, emotions])
                except Exception as e:
                    frame_results.append([current_time_str, roi_name, "Error", {}])
                    logging.error(f"Error analyzing ROI '{roi_name}': {e}")

            results.extend(frame_results)
            save_results()
            time.sleep(SCREENSHOT_INTERVAL)

def run_tkinter_app():
    """Startet die tkinter-Anwendung"""
    root = tk.Tk()
    root.withdraw()
    while True:
        task = tkinter_queue.get()
        if task is None:
            break
        try:
            task()
        except Exception as e:
            logging.error(f"Error in tkinter task: {e}")
        finally:
            tkinter_queue.task_done()

if __name__ == '__main__':
    tkinter_thread = threading.Thread(target=run_tkinter_app)
    tkinter_thread.start()
    app.run(port=5000, use_reloader=False)
