from pyAudioAnalysis import audioSegmentation as aS

# Pfad zur Audiodatei
audio_path = "temp_audio.wav"

# Segmentiere und klassifiziere das Audio (vortrainiertes Modell wird verwendet)
aS.mtFileClassification(audio_path, "pyAudioAnalysis/data/models/svmGender", "svm")
