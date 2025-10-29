import speech_recognition as sr
from pydub import AudioSegment

AudioSegment.converter = "C:\\ffmpeg\\ffmpeg.exe"
AudioSegment.ffmpeg = "C:\\ffmpeg\\ffmpeg.exe"
AudioSegment.ffprobe = "C:\\ffmpeg\\ffprobe.exe"
import io


def convert(audio_file):
    try:
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
                return text
                # print("Transcription:")
                # print(text)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
                return "Could not understand audio"
            except sr.RequestError as e:
                print(
                    f"Could not request results from Google Speech Recognition service; {e}"
                )
                return "Speech recognition service error"
    except FileNotFoundError:
        print(f"Audio file {audio_file} not found, returning mock text")
        return "Turn left at the next intersection"
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return "Audio processing error"