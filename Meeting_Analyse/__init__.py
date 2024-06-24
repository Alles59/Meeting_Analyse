from otree.api import *
import threading
import os
import json

doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'Meeting_Analyse'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    analyse_audio = models.BooleanField(choices=[
        [False, 'off'],
        [True, 'on'],
    ])
    video_path = models.StringField()

def extract_audio(video_path):
    abs_video_path = os.path.abspath(video_path)
    os.system(f'python extract_audio.py "{abs_video_path}"')
    analyze_audio(abs_video_path)

def analyze_audio(video_path):
    abs_video_path = os.path.abspath(video_path)
    output_path = os.path.join(os.path.dirname(__file__), 'audio_analysis.json')
    os.system(f'python Echtzeit-Videoaudio.py "{abs_video_path}" "{output_path}"')

class MyPage(Page):
    form_model = 'player'
    form_fields = ['analyse_audio', 'video_path']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.analyse_audio:
            threading.Thread(target=extract_audio, args=(player.video_path,)).start()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            "video_path": f"/static/videos/{os.path.basename(player.video_path)}"
        }

page_sequence = [MyPage, Results]
