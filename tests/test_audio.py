from io import BytesIO
import os
import wave
import pytest
from call_insights.audio import AudioValidationError, validate_audio, temporary_audio, cleanup_stale_audio


def wav(seconds=1):
    output = BytesIO()
    with wave.open(output, 'wb') as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(8000)
        recording.writeframes(b'\x00\x00' * int(seconds * 8000))
    return output.getvalue()


def test_actual_wav_and_limits():
    data = wav()
    info = validate_audio(data, '../../call.WAV')
    assert info.duration_seconds == 1
    assert info.format == 'wav'
    assert info.size_bytes == len(data)
    for kwargs in [{'max_bytes': 100}, {'max_seconds': .5}]:
        with pytest.raises(AudioValidationError):
            validate_audio(data, 'call.wav', **kwargs)


@pytest.mark.parametrize('data,name',[(b'', 'a.wav'),(b'not audio','a.wav'),(b'not audio','a.mp3'),(wav(),'a.exe'),(wav()[:-20],'a.wav'),(wav(0),'a.wav')], ids=['empty', 'fake-wav', 'fake-mp3', 'extension', 'truncated', 'zero-frames'])
def test_invalid_recordings(data,name):
    with pytest.raises(AudioValidationError):
        validate_audio(data,name)


def test_temporary_cleanup_on_failure(tmp_path):
    with pytest.raises(RuntimeError):
        with temporary_audio(wav(),'wav',tmp_path) as path:
            assert path.parent == tmp_path
            assert path.read_bytes() == wav()
            raise RuntimeError('service failed')
    assert not path.exists()


def test_stale_cleanup_preserves_recent_and_unrelated(tmp_path):
    unrelated = tmp_path / 'recording.wav'
    unrelated.write_bytes(b'keep')
    old = tmp_path / 'call-insights-old.wav'
    old.write_bytes(b'old')
    os.utime(old,(1,1))
    recent = tmp_path / 'call-insights-recent.wav'
    recent.write_bytes(b'new')
    assert cleanup_stale_audio(tmp_path) == 1
    assert unrelated.exists() and recent.exists()
