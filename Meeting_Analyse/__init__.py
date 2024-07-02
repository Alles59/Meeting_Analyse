from otree.api import *
import threading
import os

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
    video_path = models.StringField()

def extract_audio_and_analyze(video_path):
    abs_video_path = os.path.abspath(video_path)
    audio_output_path = os.path.join(os.path.dirname(__file__), 'audio_analysis.json')
    filler_output_path = os.path.join(os.path.dirname(__file__), 'filler_word_analysis.json')
    
    # Run audio analysis
    os.system(f'python Echtzeit-Videoaudio.py "{abs_video_path}" "{audio_output_path}"')
    
    # Run filler word analysis
    os.system(f'python Transkribition_live.py "{abs_video_path}" "{filler_output_path}"')

class MyPage(Page):
    form_model = 'player'
    form_fields = ['video_path']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        threading.Thread(target=extract_audio_and_analyze, args=(player.video_path,)).start()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            "video_path": f"/static/videos/{os.path.basename(player.video_path)}"
        }

page_sequence = [MyPage, Results]
