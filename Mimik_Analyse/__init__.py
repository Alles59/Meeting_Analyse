import threading  # Importiert das threading-Modul für die Erstellung von Nebenläufigkeit
import atexit  # Importiert das atexit-Modul, um Funktionen beim Programmende auszuführen
import time  # Importiert das time-Modul für Zeitverzögerungen
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Page
)  # Importiert die notwendigen Klassen und Funktionen aus der oTree-Bibliothek

class Constants(BaseConstants):
    # Definiert Konstanten für die App
    name_in_url = 'emotion_analysis'  # Name der App in der URL
    players_per_group = None  # Anzahl der Spieler pro Gruppe (keine Gruppierung)
    num_rounds = 1  # Anzahl der Runden

class Subsession(BaseSubsession):
    # Subsession-Klasse zur Verwaltung der Spielsitzung
    pass

class Group(BaseGroup):
    # Group-Klasse zur Verwaltung der Gruppeninteraktionen
    pass

class Player(BasePlayer):
    # Player-Klasse zur Verwaltung der Spielerinformationen
    pass

class StartPage(Page):
    # Startseite der App
    def is_displayed(self):
        # Überprüft, ob die Seite angezeigt werden soll (nur in der ersten Runde)
        return self.round_number == 1

    def vars_for_template(self):
        # Definiert Variablen für das Template der Startseite
        return {
            'results_url': 'http://localhost:5000/results',  # URL für die Ergebnisse
            'bar_chart_url': 'http://localhost:5000/bar_chart.png',  # URL für das Balkendiagramm
        }

# Definiert die Reihenfolge der Seiten in der App
page_sequence = [StartPage]

def run_flask():
    # Startet den Flask-Server
    import flask_server  # Importiert das Flask-Server-Modul
    flask_server.app.run(port=5000, use_reloader=False)  # Startet den Server auf Port 5000

def start_flask_app():
    # Startet die Flask-App in einem separaten Thread
    flask_thread = threading.Thread(target=run_flask)  # Erstellt einen neuen Thread für den Flask-Server
    flask_thread.daemon = True  # Markiert den Thread als Daemon, damit er beim Programmende automatisch beendet wird
    flask_thread.start()  # Startet den Flask-Thread
    atexit.register(lambda: flask_thread.join())  # Registriert eine Funktion, die beim Programmende ausgeführt wird, um sicherzustellen, dass der Thread beendet wird

if __name__ == '__main__':
    start_flask_app()  # Startet die Flask-App
    # Verzögerung, um sicherzustellen, dass Flask vor oTree startet
    time.sleep(10)
