from otree.api import *
import threading
import os

doc = """
Audio Analysis Experiment
"""

class C(BaseConstants):
    NAME_IN_URL = 'audio_analysis'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    pass

def start_audio_capture():
    os.system('python capture_audio.py')

def start_audio_analysis():
    os.system('python audio_analysis.py')

class MyPage(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        threading.Thread(target=start_audio_capture).start()
        threading.Thread(target=start_audio_analysis).start()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {}

page_sequence = [MyPage, Results]
