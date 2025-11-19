import os
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure FFmpeg paths from environment variables (platform-specific)
# On Windows, these should point to the FFmpeg executables
# On Linux/Mac, FFmpeg should be in PATH
import shutil
import platform

def find_ffmpeg():
    """Find FFmpeg executable in system PATH or common locations"""
    # First check environment variables
    ffmpeg_path = os.environ.get("FFMPEG_PATH", "")
    ffmpeg_exe = os.environ.get("FFMPEG_EXE", "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
    ffprobe_exe = os.environ.get("FFPROBE_EXE", "ffprobe.exe" if platform.system() == "Windows" else "ffprobe")
    
    if ffmpeg_path:
        ffmpeg_full = os.path.join(ffmpeg_path, ffmpeg_exe)
        ffprobe_full = os.path.join(ffmpeg_path, ffprobe_exe)
        if os.path.exists(ffmpeg_full) and os.path.exists(ffprobe_full):
            return ffmpeg_full, ffprobe_full
    
    # Try to find in PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    ffprobe_in_path = shutil.which("ffprobe")
    
    if ffmpeg_in_path and ffprobe_in_path:
        return ffmpeg_in_path, ffprobe_in_path
    
    # Try common Windows locations
    if platform.system() == "Windows":
        common_paths = [
            (r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\ffmpeg\bin\ffprobe.exe"),
            (r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffprobe.exe"),
            (os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"), os.path.expanduser(r"~\ffmpeg\bin\ffprobe.exe")),
        ]
        for ffmpeg_path, ffprobe_path in common_paths:
            if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
                return ffmpeg_path, ffprobe_path
    
    # Fallback to just the executable name (will fail if not in PATH)
    return ffmpeg_exe, ffprobe_exe

# Find and set FFmpeg paths
ffmpeg_path, ffprobe_path = find_ffmpeg()
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

print(f"[Audio] FFmpeg configured: {ffmpeg_path}")
print(f"[Audio] FFprobe configured: {ffprobe_path}")

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
            - Audio file not found: Returns ""
            - Recognition fails: Returns "Could not understand audio"
            - API error: Returns "Speech recognition service error"
            - Other errors: Returns "Audio processing error"
    
    Note:
        Requires FFmpeg to be installed and configured (via environment variables
        or system PATH). Network connection required for Google Speech Recognition API.
    """
    try:
        # Load and preprocess audio
        print(f"[Audio] Loading audio file: {audio_file}")
        audio = AudioSegment.from_file(audio_file)
        
        # Check audio duration
        duration_ms = len(audio)
        duration_sec = duration_ms / 1000.0
        print(f"[Audio] Audio duration: {duration_sec:.2f} seconds")
        
        if duration_sec < 0.1:
            print(f"[Audio] Warning: Audio file is too short ({duration_sec:.2f}s), may not be recognized")
            return "Could not understand audio: Audio too short"
        
        # Preprocess audio for better recognition
        # 1. Normalize volume (boost quiet audio)
        if audio.max_possible_amplitude > 0:
            normalized_audio = audio.normalize()
        else:
            normalized_audio = audio
        
        # 2. Set to mono channel (required by Google Speech Recognition)
        if normalized_audio.channels > 1:
            normalized_audio = normalized_audio.set_channels(1)
        
        # 3. Set sample rate to 16kHz (optimal for speech recognition)
        normalized_audio = normalized_audio.set_frame_rate(16000)
        
        # 4. Adjust volume if too quiet (boost by 10dB if max volume is low)
        max_dBFS = normalized_audio.max_dBFS
        print(f"[Audio] Original audio level: {max_dBFS:.1f} dBFS")
        
        # More aggressive volume boosting for quiet audio
        if max_dBFS < -30:  # Very quiet
            print(f"[Audio] Audio is very quiet ({max_dBFS:.1f} dBFS), boosting by 20dB")
            normalized_audio = normalized_audio + 20
        elif max_dBFS < -20:  # Quiet
            print(f"[Audio] Audio is quiet ({max_dBFS:.1f} dBFS), boosting by 15dB")
            normalized_audio = normalized_audio + 15
        elif max_dBFS < -15:  # Slightly quiet
            print(f"[Audio] Audio is slightly quiet ({max_dBFS:.1f} dBFS), boosting by 10dB")
            normalized_audio = normalized_audio + 10
        
        # Re-check volume after boosting
        max_dBFS_after = normalized_audio.max_dBFS
        print(f"[Audio] Audio level after boosting: {max_dBFS_after:.1f} dBFS")
        
        # Convert to WAV format
        audio_wav = io.BytesIO()
        normalized_audio.export(audio_wav, format="wav", parameters=["-ac", "1", "-ar", "16000"])
        audio_wav.seek(0)
        print(f"[Audio] Audio preprocessed: mono, 16kHz, normalized")

        # Transcribe the audio using SpeechRecognition
        # Try multiple recognition attempts with different settings
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_wav) as source:
            # Try different energy threshold settings
            recognition_attempts = [
                {"energy_threshold": 300, "dynamic": True, "adjust_noise": True},
                {"energy_threshold": 400, "dynamic": True, "adjust_noise": False},
                {"energy_threshold": 200, "dynamic": False, "adjust_noise": False},
            ]
            
            for attempt_num, settings in enumerate(recognition_attempts, 1):
                try:
                    print(f"[Audio] Recognition attempt {attempt_num}/{len(recognition_attempts)}")
                    recognizer.energy_threshold = settings["energy_threshold"]
                    recognizer.dynamic_energy_threshold = settings["dynamic"]
                    
                    # Reset file pointer
                    audio_wav.seek(0)
                    
                    # Adjust for ambient noise if enabled
                    if settings["adjust_noise"] and duration_sec > 1.0:
                        try:
                            print(f"[Audio] Adjusting for ambient noise...")
                            recognizer.adjust_for_ambient_noise(source, duration=min(1.0, duration_sec * 0.3))
                            audio_wav.seek(0)  # Reset after noise adjustment
                        except Exception as e:
                            print(f"[Audio] Noise adjustment failed: {e}, continuing anyway")
                            audio_wav.seek(0)
                    
                    audio_data = recognizer.record(source)
                    print(f"[Audio] Sending audio to Google Speech Recognition API (attempt {attempt_num})...")
                    
                    # Try with different language models
                    recognition_options = [
                        {"language": "en-US", "show_all": False},
                        {"language": "en-US", "show_all": True},
                    ]
                    
                    for opt in recognition_options:
                        try:
                            if opt["show_all"]:
                                # Try with show_all to get alternative results
                                result = recognizer.recognize_google(audio_data, language=opt["language"], show_all=True)
                                if result and 'alternative' in result and len(result['alternative']) > 0:
                                    text = result['alternative'][0]['transcript']
                                    confidence = result['alternative'][0].get('confidence', 0.0)
                                    print(f"[Audio] Transcription successful (confidence: {confidence:.2f}): '{text}'")
                                    return text
                            else:
                                text = recognizer.recognize_google(audio_data, language=opt["language"])
                                print(f"[Audio] Transcription successful: '{text}'")
                                return text
                        except sr.UnknownValueError:
                            print(f"[Audio] Attempt {attempt_num} failed: Could not understand audio")
                            continue
                        except sr.RequestError as e:
                            print(f"[Audio] Request error on attempt {attempt_num}: {e}")
                            # Don't retry on network errors
                            raise
                    
                except sr.RequestError as e:
                    print(f"[Audio] Error: Could not request results from Google Speech Recognition service")
                    print(f"[Audio] Service error: {e}")
                    print(f"[Audio] Possible causes: network issue, API quota exceeded, or service unavailable")
                    return "Speech recognition service error"
                except Exception as e:
                    print(f"[Audio] Unexpected error on attempt {attempt_num}: {e}")
                    continue
            
            # All attempts failed
            print(f"[Audio] All recognition attempts failed")
            print(f"[Audio] Audio stats: duration={duration_sec:.2f}s, max_dBFS={max_dBFS:.1f}, after_boost={max_dBFS_after:.1f}")
            print(f"[Audio] Possible causes:")
            print(f"[Audio]   - Audio file may not contain clear speech")
            print(f"[Audio]   - Audio may be too quiet or corrupted")
            print(f"[Audio]   - Background noise may be interfering")
            print(f"[Audio]   - Audio format may not be compatible")
            return "Could not understand audio"
    except FileNotFoundError:
        print(f"[Audio] Error: Audio file {audio_file} not found")
        return ""
    except Exception as e:
        print(f"[Audio] Error processing audio file: {e}")
        import traceback
        traceback.print_exc()
        return "Audio processing error"


def test_audio_file(audio_file):
    """
    Test function to diagnose audio file issues.
    Prints detailed information about the audio file.
    """
    try:
        print(f"\n[Audio Test] Analyzing: {audio_file}")
        audio = AudioSegment.from_file(audio_file)
        
        print(f"[Audio Test] Duration: {len(audio) / 1000.0:.2f} seconds")
        print(f"[Audio Test] Channels: {audio.channels}")
        print(f"[Audio Test] Sample rate: {audio.frame_rate} Hz")
        print(f"[Audio Test] Sample width: {audio.sample_width} bytes")
        print(f"[Audio Test] Frame count: {audio.frame_count()}")
        print(f"[Audio Test] Max possible amplitude: {audio.max_possible_amplitude}")
        print(f"[Audio Test] Max dBFS: {audio.max_dBFS:.1f} dB")
        print(f"[Audio Test] RMS: {audio.rms:.1f}")
        
        # Try to convert
        result = convert(audio_file)
        print(f"[Audio Test] Recognition result: '{result}'")
        return result
        
    except Exception as e:
        print(f"[Audio Test] Error: {e}")
        import traceback
        traceback.print_exc()
        return None