import os
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure FFmpeg paths from environment variables (platform-specific)
# On Windows, these should point to the FFmpeg executables
# On Linux/Mac, FFmpeg should be in PATH
ffmpeg_path = os.environ.get("FFMPEG_PATH", "")
ffmpeg_exe = os.environ.get("FFMPEG_EXE", "ffmpeg")
ffprobe_exe = os.environ.get("FFPROBE_EXE", "ffprobe")

# Set FFmpeg paths if explicitly provided (mainly for Windows)
if ffmpeg_path:
    AudioSegment.converter = os.path.join(ffmpeg_path, ffmpeg_exe)
    AudioSegment.ffmpeg = os.path.join(ffmpeg_path, ffmpeg_exe)
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, ffprobe_exe)
else:
    # Try to use system FFmpeg (Linux/Mac or if in PATH on Windows)
    AudioSegment.converter = ffmpeg_exe
    AudioSegment.ffmpeg = ffmpeg_exe
    AudioSegment.ffprobe = ffprobe_exe

import io


def convert(audio_file):
    """
    Convert audio file to text using speech recognition.
    
    This function processes audio files (MP3, WAV, etc.) and converts them to text
    using Google Speech Recognition API. The audio is first converted to WAV format
    using FFmpeg for compatibility.
    
    Args:
        audio_file (str): Path to the audio file to process
        
    Returns:
        str: Transcribed text from the audio file, or error message string if:
            - Audio file not found: Returns mock text "Turn left at the next intersection"
            - Recognition fails: Returns "Could not understand audio"
            - API error: Returns "Speech recognition service error"
            - Other errors: Returns "Audio processing error"
    
    Note:
        Requires FFmpeg to be installed and configured (via environment variables
        or system PATH). Network connection required for Google Speech Recognition API.
    """
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