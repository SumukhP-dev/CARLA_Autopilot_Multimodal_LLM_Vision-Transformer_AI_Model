import speech_recognition as sr
from pydub import AudioSegment

AudioSegment.converter = "C:\\ffmpeg\\ffmpeg.exe"
AudioSegment.ffmpeg = "C:\\ffmpeg\\ffmpeg.exe"
AudioSegment.ffprobe = "C:\\ffmpeg\\ffprobe.exe"
import io


class audioConversion:
    def __init__(self):
        pass

    def convert(self, audio_file):
        # Convert to WAV format if needed
        audio = AudioSegment.from_file(audio_file)
        audio_wav = io.BytesIO()
        audio.export(audio_wav, format="wav")
        audio_wav.seek(0)

        # Transcribe the audio using SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_wav) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                transcribed_audio_file.append(text)
                # print("Transcription:")
                # print(text)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                print(
                    f"Could not request results from Google Speech Recognition service; {e}"
                )
