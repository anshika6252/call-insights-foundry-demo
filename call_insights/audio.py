"""Content-aware recording validation and short-lived private audio files."""
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tempfile
import wave


class AudioValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AudioInfo:
    duration_seconds: float
    format: str
    sha256: str
    size_bytes: int


def validate_audio(data: bytes, filename: str, max_bytes: int = 50 * 1024 * 1024,
                   max_seconds: float = 600) -> AudioInfo:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".wav", ".mp3"}:
        raise AudioValidationError("Choose a WAV or MP3 recording.")
    if not data:
        raise AudioValidationError("The recording is empty.")
    if len(data) > max_bytes:
        raise AudioValidationError("The recording exceeds the upload size limit.")
    try:
        if suffix == ".wav":
            with wave.open(BytesIO(data), "rb") as recording:
                frames = recording.getnframes()
                frame_size = recording.getnchannels() * recording.getsampwidth()
                duration = frames / recording.getframerate()
                if len(recording.readframes(frames)) != frames * frame_size:
                    raise AudioValidationError("The WAV recording is truncated.")
        else:
            from mutagen.mp3 import MP3
            recording = MP3(BytesIO(data))
            duration = recording.info.length
    except AudioValidationError:
        raise
    except Exception as exc:
        raise AudioValidationError("The file is not a readable WAV or MP3 recording.") from exc
    if duration <= 0:
        raise AudioValidationError("The recording contains no audio frames.")
    if duration > max_seconds:
        raise AudioValidationError("The recording exceeds the duration limit.")
    return AudioInfo(duration, suffix[1:], sha256(data).hexdigest(), len(data))


@contextmanager
def temporary_audio(data: bytes, audio_format: str, directory: str | Path | None = None):
    """Yield a generated path, removing it on both successful and failed processing."""
    if audio_format not in {"wav", "mp3"}:
        raise AudioValidationError("Unsupported audio format.")
    if directory is not None:
        Path(directory).mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="call-insights-", suffix="." + audio_format,
                                     dir=directory, delete=False) as handle:
        path = Path(handle.name)
        try:
            handle.write(data)
        except BaseException:
            handle.close()
            path.unlink(missing_ok=True)
            raise
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def cleanup_stale_audio(directory: str | Path, max_age_seconds: float = 86400) -> int:
    """Remove only generated audio files older than the configured retention window."""
    import time
    count = 0
    for path in Path(directory).glob("call-insights-*"):
        if path.suffix in {".wav", ".mp3"} and path.is_file() and not path.is_symlink():
            if time.time() - path.stat().st_mtime > max_age_seconds:
                path.unlink(missing_ok=True)
                count += 1
    return count
