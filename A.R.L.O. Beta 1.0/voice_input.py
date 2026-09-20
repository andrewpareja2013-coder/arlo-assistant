# =============================================================
# VOICE_INPUT.PY
# Handles speech-to-text (microphone recording + transcription)
# and text-to-speech (spoken replies), for voice command support.
# =============================================================

import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import win32com.client
import config
import security

_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("Loading speech recognition model...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


def record_audio(duration=5, samplerate=16000):
    if config.TEST_MODE and security.can_see_debug():
        print(f"Listening for {duration} seconds...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32", device=config.MICROPHONE_DEVICE)
    sd.wait()
    return audio, samplerate


def transcribe(audio, samplerate):
    """Converts recorded audio into text."""
    model = _get_whisper_model()
    audio_flat = audio.flatten()
    segments, info = model.transcribe(audio_flat, language="en")
    text = " ".join(segment.text for segment in segments)
    return text.strip()


def speak(text):
    """Speaks text aloud using Windows' built-in speech engine.
    Creates a fresh engine each call -- reusing one causes it to go
    silent after the first use (a known SAPI5/pyttsx3 reliability issue)."""
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception:
        pass

def listen_for_wake_word(callback, wake_word="arlo", chunk_duration=3):
    while True:
        audio, sr = record_audio(duration=chunk_duration)
        text = transcribe(audio, sr)

        if wake_word in text.lower():
            print("\n🎤 Listening...")
            command_audio, command_sr = record_until_silence()
            command_text = transcribe(command_audio, command_sr)

            cleaned = command_text.strip()
            word_count = len(cleaned.split())

            if word_count >= 3:
                callback(cleaned)
            elif cleaned:
                print(f"(Command too short or unclear, ignored: '{cleaned}')")

def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        if config.TEST_MODE and security.can_see_debug():
            print("Loading speech recognition model...")
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model

def list_microphones():
    """Lists available microphone devices."""
    devices = sd.query_devices()
    mics = [(i, d["name"]) for i, d in enumerate(devices) if d["max_input_channels"] > 0]
    return mics

def record_until_silence(samplerate=16000, silence_threshold=0.02, silence_duration=1.2, max_duration=15):
    """
    Records audio until the user stops talking (volume drops below
    threshold for silence_duration seconds), or max_duration is reached.
    """
    chunk_size = int(samplerate * 0.1)  # 100ms chunks
    recorded_chunks = []
    silent_chunks_needed = int(silence_duration / 0.1)
    silent_chunk_count = 0
    has_spoken = False

    with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32") as stream:
        total_samples = 0
        max_samples = int(max_duration * samplerate)

        while total_samples < max_samples:
            chunk, _ = stream.read(chunk_size)
            recorded_chunks.append(chunk)
            total_samples += chunk_size

            volume = np.abs(chunk).mean()

            if volume > silence_threshold:
                has_spoken = True
                silent_chunk_count = 0
            elif has_spoken:
                silent_chunk_count += 1
                if silent_chunk_count >= silent_chunks_needed:
                    break

    audio = np.concatenate(recorded_chunks)
    return audio, samplerate

if __name__ == "__main__":
    for index, name in list_microphones():
        print(f"{index}: {name}")