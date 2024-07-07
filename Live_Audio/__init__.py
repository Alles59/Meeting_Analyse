from otree.api import *
import threading
from .audio_capture_analysis import start_recording, stop_recording, stop_event

class Constants(BaseConstants):
    name_in_url = 'audio_analysis'
    players_per_group = None
    num_rounds = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    pass

class Results(Page):
    @staticmethod
    def vars_for_template(player):
        # Start the recording thread as a daemon thread
        stop_event.clear()
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.daemon = True
        recording_thread.start()

    @staticmethod
    def before_next_page(player, timeout_happened):
        # Stop the recording thread
        stop_recording()

page_sequence = [Results]
