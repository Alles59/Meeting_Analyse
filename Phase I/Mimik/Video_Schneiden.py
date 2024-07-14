import cv2  # Import der OpenCV-Bibliothek für die Videobearbeitung

# Initialisierung der Variablen
drawing = False  # Flag, um den Zeichenstatus zu verfolgen
ix, iy = -1, -1  # Initialisierung der Startkoordinaten des Rechtecks
ex, ey = -1, -1  # Initialisierung der Endkoordinaten des Rechtecks

def draw_rectangle(event, x, y, flags, param):
    """Callback-Funktion zum Zeichnen eines Rechtecks auf dem Bild basierend auf Mausereignissen."""
    global ix, iy, ex, ey, drawing

    if event == cv2.EVENT_LBUTTONDOWN:  # Linke Maustaste gedrückt
        drawing = True  # Zeichnen starten
        ix, iy = x, y  # Startkoordinaten speichern

    elif event == cv2.EVENT_MOUSEMOVE:  # Maus bewegt sich
        if drawing:  # Wenn die linke Maustaste gedrückt ist
            img_copy = img.copy()  # Kopie des Bildes erstellen
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)  # Rechteck zeichnen
            cv2.imshow('image', img_copy)  # Bild mit Rechteck anzeigen

    elif event == cv2.EVENT_LBUTTONUP:  # Linke Maustaste losgelassen
        drawing = False  # Zeichnen beenden
        ex, ey = x, y  # Endkoordinaten speichern
        cv2.rectangle(img, (ix, iy), (ex, ey), (0, 255, 0), 2)  # Endgültiges Rechteck zeichnen

# Öffnen des Videos
video_path = "C:/Users/.../.../.../.mp4"  # Pfad zur Videodatei
output_folder = "C:/Users/.../.../.../"  # Ausgabeverzeichnis
cap = cv2.VideoCapture(video_path)  # VideoCapture-Objekt initialisieren

ret, img = cap.read()  # Erstes Frame lesen
if not ret:  # Überprüfung, ob das Lesen des Videos erfolgreich war
    print("Fehler beim Lesen des Videos")  # Fehlermeldung ausgeben
    cap.release()  # Freigabe des VideoCapture-Objekts
    cv2.destroyAllWindows()  # Schließen aller Fenster
    exit()  # Programm beenden

cv2.namedWindow('image', cv2.WINDOW_NORMAL)  # Fenster für die Bildanzeige erstellen
cv2.resizeWindow('image', img.shape[1], img.shape[0])  # Fenstergröße auf die Größe des Videos setzen
cv2.setMouseCallback('image', draw_rectangle)  # Callback-Funktion für Mausereignisse setzen

while True:
    cv2.imshow('image', img)  # Bild anzeigen
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC-Taste zum Beenden
        cap.release()  # Freigabe des VideoCapture-Objekts
        cv2.destroyAllWindows()  # Schließen aller Fenster
        exit()  # Programm beenden
    elif key == 13:  # Enter-Taste zum Bestätigen der Auswahl
        break

cv2.destroyAllWindows()  # Schließen aller Fenster

# Überprüfung, ob gültige Koordinaten ausgewählt wurden
if ix == -1 or iy == -1 or ex == -1 or ey == -1:
    print("Kein gültiger Bereich ausgewählt")  # Fehlermeldung ausgeben
    cap.release()  # Freigabe des VideoCapture-Objekts
    cv2.destroyAllWindows()  # Schließen aller Fenster
    exit()  # Programm beenden

# Definition des ausgewählten Bereichs
x1, y1 = min(ix, ex), min(iy, ey)  # Berechnung der oberen linken Ecke
x2, y2 = max(ix, ex), max(iy, ey)  # Berechnung der unteren rechten Ecke

# Initialisierung des VideoWriter-Objekts
frame_width = x2 - x1  # Breite des ausgewählten Bereichs
frame_height = y2 - y1  # Höhe des ausgewählten Bereichs
frame_rate = cap.get(cv2.CAP_PROP_FPS)  # Bildrate des Videos
output_path = f"{output_folder}cut_segment.mp4"  # Pfad für die Ausgabedatei
out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), frame_rate, (frame_width, frame_height))  # VideoWriter-Objekt

# Ausschneiden und Speichern des ausgewählten Videobereichs
cap = cv2.VideoCapture(video_path)  # VideoCapture-Objekt neu initialisieren
while True:
    ret, frame = cap.read()  # Frame lesen
    if not ret:
        break  # Beenden, wenn keine weiteren Frames verfügbar sind

    segment_frame = frame[y1:y2, x1:x2]  # Ausschneiden des ausgewählten Bereichs
    out.write(segment_frame)  # Schreiben des ausgeschnittenen Bereichs in die Ausgabedatei

cap.release()  # Freigabe des VideoCapture-Objekts
out.release()  # Freigabe des VideoWriter-Objekts
cv2.destroyAllWindows()  # Schließen aller Fenster

print(f"Das ausgeschnittene Video wurde in {output_path} gespeichert.")  # Erfolgsnachricht ausgeben
