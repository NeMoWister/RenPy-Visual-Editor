"""
Извлечение "пиков" (waveform) аудиофайла для визуализации в редакторе
(см. ui/waveform_widget.py - используется в полях play_music/play_sound/
play_ambience для точной расстановки fadein/fadeout).

Используем ffmpeg (если он есть в PATH) для декодирования ЛЮБОГО формата
(mp3/ogg/wav/flac/opus) в сырой mono PCM16 WAV во временный файл, который
затем читается стандартным модулем `wave` - сознательно НЕ лезем во
внутренние буферы QAudioDecoder/QAudioBuffer напрямую: это избавляет от
возни с сырыми указателями и различиями между версиями PyQt6/Qt6 на разных
платформах, за которые тут особо не с чем свериться.

Если ffmpeg не найден или конвертация не удалась - возвращаем пустой
список; это не ошибка: сама волна тогда просто не рисуется, но плеер,
перемотка по клику и маркеры fadein/fadeout продолжают работать как обычно
(длительность трека даёт общий QMediaPlayer - см. ui/audio_preview.py).
"""
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from typing import List

_ffmpeg_checked = False
_ffmpeg_path: str = ""


def _creation_flags() -> int:
    """На Windows не даёт subprocess мигать чёрным окном консоли (особенно
    заметно в собранном .exe - там это единственное, что вообще видно)."""
    if os.name == "nt":
        return subprocess.CREATE_NO_WINDOW
    return 0


def _find_ffmpeg() -> str:
    global _ffmpeg_checked, _ffmpeg_path
    if not _ffmpeg_checked:
        _ffmpeg_path = shutil.which("ffmpeg") or ""
        _ffmpeg_checked = True
    return _ffmpeg_path


def ffmpeg_available() -> bool:
    return bool(_find_ffmpeg())


def extract_peaks(path: str, num_buckets: int = 600, timeout_sec: float = 15.0) -> List[float]:
    """Возвращает до num_buckets чисел в диапазоне [0.0, 1.0] - пиковую
    амплитуду в каждом временном отрезке трека (по всей длине файла).
    Пустой список означает "волна недоступна" (нет ffmpeg / файл не
    декодировался / файл пуст) - вызывающая сторона должна на этот случай
    рисовать плоскую линию-заглушку, а не падать."""
    if not path or not os.path.isfile(path):
        return []

    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        return []

    tmp_wav = ""
    try:
        fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        result = subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-i", path,
             "-ac", "1", "-ar", "22050", "-f", "wav", tmp_wav],
            capture_output=True, timeout=timeout_sec,
            creationflags=_creation_flags(),
        )
        if result.returncode != 0 or not os.path.isfile(tmp_wav) or os.path.getsize(tmp_wav) == 0:
            return []

        with wave.open(tmp_wav, "rb") as wf:
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            if n_frames <= 0 or sampwidth not in (1, 2, 4):
                return []
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            count = len(raw) // 2
            if count == 0:
                return []
            samples = struct.unpack(f"<{count}h", raw[:count * 2])
            max_val = 32768.0
        elif sampwidth == 1:
            if not raw:
                return []
            samples = [b - 128 for b in raw]
            max_val = 128.0
        else:                                       
            count = len(raw) // 4
            if count == 0:
                return []
            samples = struct.unpack(f"<{count}i", raw[:count * 4])
            max_val = float(2 ** 31)

        bucket_size = max(1, len(samples) // max(1, num_buckets))
        peaks: List[float] = []
        for i in range(0, len(samples), bucket_size):
            chunk = samples[i:i + bucket_size]
            if not chunk:
                continue
            peak = max(abs(s) for s in chunk) / max_val
            peaks.append(min(1.0, peak))
        return peaks[:num_buckets] if peaks else []
    except Exception:
        return []
    finally:
        if tmp_wav and os.path.isfile(tmp_wav):
            try:
                os.remove(tmp_wav)
            except OSError:
                pass
