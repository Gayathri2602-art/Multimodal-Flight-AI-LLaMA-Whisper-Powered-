"""
utils/audio.py
--------------
Thin wrappers around Whisper (ASR) and gTTS (TTS).

Public API
----------
    transcribe(audio_path, asr_pipe) -> str
    tts(text)                        -> str  (path to mp3 temp file)
"""

from __future__ import annotations

import tempfile

import numpy as np


def transcribe(audio_path: str | None, asr_pipe) -> str:
    """
    Transcribe an audio file using the Whisper pipeline.

    Parameters
    ----------
    audio_path : Local path to audio file (wav / mp3 / etc.)
    asr_pipe   : Hugging Face ASR pipeline (transformers.pipeline)

    Returns
    -------
    Transcribed text, or empty string on failure.
    """
    if not audio_path:
        return ""

    try:
        import librosa  # lazy import — not needed in every environment

        audio, _ = librosa.load(audio_path, sr=16_000)
        result   = asr_pipe(audio)

        if isinstance(result, dict):
            return result.get("text", "").strip()
        return str(result).strip()

    except Exception as exc:
        print(f"[audio] ASR error: {exc}")
        return ""


def tts(text: str) -> str | None:
    """
    Convert text to speech using gTTS and save to a temp mp3 file.

    Returns
    -------
    Path to the generated mp3, or None on failure.
    """
    try:
        from gtts import gTTS  # lazy import

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        gTTS(text).save(tmp.name)
        return tmp.name

    except Exception as exc:
        print(f"[audio] TTS error: {exc}")
        return None
