Project Description

  Meeting Analyse is an oTree-based tool that includes three separate apps designed to analyze meeting dynamics using audio and video data. 
  It leverages natural language processing (NLP) and audio analysis techniques to provide insights on stress levels, monotony, harmonic-to-noise ratio (HNR), speech clarity, fillerwords and emotions.

Installation

  bash

    git clone https://github.com/Alles59/Meeting_Analyse.git

Install the required dependencies:

  bash

    pip install -r requirements.txt

Usage:

  Go to the directory 

    cd Meeting_Analyse 
    
  in your projekt.

  bash

    otree devserver

  Access the oTree apps via your web browser at http://localhost:8000.

  Audio Live for Windows:
    For the Audio Live App you have to enable Stereo Mix in your system settings. 

  Mimik Live:
  Additionaly to the Otree server you have to start the flask server with.

  bash

    pyhton flask_server.py

Apps Overview

   Meeting Analyse
        Extracts Audio from a video and analyses it for paraverbal and verbal features.

  Audio Live
        Extracts Audio from the microphone and the system audio.

  Live Transcription
        Extracts the emotions from the facial expressions, for several people.
        
Features
    Stress Analysis
    Monotony Detection
    Speech Clarity
    Speech Harmonicy
    Audio extraction
    Filler Word Detection
    Emotion detection

