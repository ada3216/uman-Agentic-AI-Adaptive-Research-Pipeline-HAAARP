"""
Transcription Adapter — local WhisperX integration.

LOCAL ONLY. No cloud transcription services (AssemblyAI, Deepgram etc.)
These would transmit audio to external servers, violating DPIA for special_category data.

Output format: transcript.json with timestamps, speaker tags, and segment IDs
compatible with grounding_checker anchor format:
  Text segments: { "segment_id": "P01_session1_seg_042", "speaker": "P01", "text": "..." }
  Audio anchors: P01_session1_T00:04:12_T00:04:28_pause_3200ms
"""
import sys
from pathlib import Path


def transcribe(audio_path: str, config: dict = None) -> dict:
    """
    Transcribes audio file using WhisperX running locally.
    Returns transcript dict with segments, speaker tags, and timestamps.

    WhisperX installation: pip install whisperx
    Requires: local GPU or CPU (slower). No API key needed.

    Output format:
    {
        "transcript_id": str,
        "source_file": str,
        "timestamp_utc": str,
        "segments": [
            {
                "segment_id": "P01_session1_seg_001",
                "speaker": "P01",
                "start_time": "00:04:12",
                "end_time": "00:04:28",
                "text": "...",
                "pause_before_ms": 3200,  # if detected
            }
        ]
    }
    """
    if not Path(audio_path).exists():
        print(f"[ERR_PREFLIGHT_MISSING] Audio file not found: {audio_path}")
        sys.exit(1)

    # TODO: implement WhisperX transcription
    # import whisperx
    # model = whisperx.load_model("large-v2", device="cuda")  # or "cpu"
    # result = model.transcribe(audio_path)
    # aligned = whisperx.align(result["segments"], ...)
    # diarized = whisperx.assign_word_speakers(diarize_model(...), aligned)

    print(f"Transcription of {audio_path}: TODO — implement WhisperX integration")
    return {"transcript_id": None, "source_file": audio_path, "segments": []}


def validate_transcript_format(transcript: dict) -> bool:
    """
    Validates that transcript segments include all fields required
    for grounding_checker anchor verification.
    """
    required_segment_fields = {"segment_id", "speaker", "text"}
    for seg in transcript.get("segments", []):
        if not required_segment_fields.issubset(seg.keys()):
            return False
    return True
