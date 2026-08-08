"""
Извлечение "пиков" (waveform) аудиофайла для визуализации в редакторе
(см. ui/waveform_widget.py - используется в полях play_music/play_sound/
play_ambience для точной расстановки fadein/fadeout).

РЕШЕНИЕ БЕЗ ВНЕШНЕГО FFMPEG: раньше файл декодировался через системный
`ffmpeg.exe` (требовал отдельной установки и наличия в PATH - частый источник
жалоб, особенно в собранном .exe). Теперь декодирование идёт только через
Python-библиотеки, без запуска внешних процессов и без системных
зависимостей - все варианты ниже ставятся одной командой pip и содержат
готовые бинарные колёса под Windows/macOS/Linux:

1. Настоящие .wav-файлы читаются напрямую стандартным модулем `wave` -
   работает всегда, без единой дополнительной зависимости.
2. Основные форматы, которые использует Ren'Py - mp3, ogg (Vorbis), flac,
   а также wav - декодируются через опциональную библиотеку `miniaudio`
   (`pip install miniaudio`). Это самодостаточный пакет: внутри статически
   собранные dr_libs/minimp3/stb_vorbis, никакого ffmpeg, libsndfile или
   другой системной установки не требуется - только сам пакет.
3. Ogg/Opus и некоторые дополнительные контейнеры, которые miniaudio не
   разбирает, декодируются через опциональную `soundfile`
   (`pip install soundfile`, обёртка над libsndfile - тоже обычный
   pip-пакет с готовыми колёсами).
4. Если ни один установленный декодер не справился с конкретным файлом
   (или ни один из пакетов не установлен вовсе) - волна просто не рисуется
   (пустой список), это не ошибка: плеер, перемотка по клику и маркеры
   fadein/fadeout продолжают работать как обычно (длительность трека даёт
   общий QMediaPlayer - см. ui/audio_preview.py), рисуется только плоская
   линия-заглушка.

Для покрытия всех основных форматов без единого системного бинарника
достаточно: `pip install miniaudio soundfile`.
"""
import os
import struct
import wave
from typing import List, Optional

_soundfile_checked = False
_soundfile_module = None
_miniaudio_checked = False
_miniaudio_module = None


def _get_soundfile():
    """Ленивый опциональный импорт soundfile - модуль может быть не
    установлен, это нормально (см. модульный docstring)."""
    global _soundfile_checked, _soundfile_module
    if not _soundfile_checked:
        try:
            import soundfile as sf
            _soundfile_module = sf
        except ImportError:
            _soundfile_module = None
        _soundfile_checked = True
    return _soundfile_module


def _get_miniaudio():
    """Ленивый опциональный импорт miniaudio - модуль может быть не
    установлен, это нормально (см. модульный docstring)."""
    global _miniaudio_checked, _miniaudio_module
    if not _miniaudio_checked:
        try:
            import miniaudio
            _miniaudio_module = miniaudio
        except ImportError:
            _miniaudio_module = None
        _miniaudio_checked = True
    return _miniaudio_module


def soundfile_available() -> bool:
    return _get_soundfile() is not None


def miniaudio_available() -> bool:
    return _get_miniaudio() is not None


def _peaks_from_samples(samples, max_val: float, num_buckets: int) -> List[float]:
    bucket_size = max(1, len(samples) // max(1, num_buckets))
    peaks: List[float] = []
    for i in range(0, len(samples), bucket_size):
        chunk = samples[i:i + bucket_size]
        if not chunk:
            continue
        peak = max(abs(s) for s in chunk) / max_val
        peaks.append(min(1.0, peak))
    return peaks[:num_buckets] if peaks else []


def _extract_peaks_wave(path: str, num_buckets: int) -> Optional[List[float]]:
    """Читает настоящий .wav-файл напрямую через стандартный модуль `wave`.
    Возвращает None (а не []), если файл не похож на валидный wav, чтобы
    вызывающая сторона могла попробовать soundfile дальше."""
    try:
        with wave.open(path, "rb") as wf:
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            n_channels = max(1, wf.getnchannels())
            if n_frames <= 0 or sampwidth not in (1, 2, 4):
                return None
            raw = wf.readframes(n_frames)
    except (wave.Error, EOFError, OSError):
        return None

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

    if n_channels > 1:
                                                                       
        samples = samples[::n_channels]

    return _peaks_from_samples(samples, max_val, num_buckets)


def _extract_peaks_miniaudio(path: str, num_buckets: int) -> List[float]:
    """Декодирует mp3/ogg(Vorbis)/flac/wav через miniaudio - статически
    собранные декодеры внутри самого пакета, никаких системных зависимостей.
    miniaudio сам определяет формат по содержимому файла, расширение роли
    не играет."""
    ma = _get_miniaudio()
    if ma is None:
        return []
    try:
        decoded = ma.decode_file(path, output_format=ma.SampleFormat.SIGNED16, nchannels=1)
        samples = decoded.samples
    except Exception:
        return []
    if not samples:
        return []
    return _peaks_from_samples(list(samples), 32768.0, num_buckets)


def _extract_peaks_soundfile(path: str, num_buckets: int) -> List[float]:
    sf = _get_soundfile()
    if sf is None:
        return []
    try:
        data, _samplerate = sf.read(path, dtype="int16", always_2d=True)
    except Exception:
        return []
    if data.size == 0:
        return []
                                                                          
    mono = data[:, 0]
    return _peaks_from_samples(mono.tolist(), 32768.0, num_buckets)


def extract_peaks(path: str, num_buckets: int = 600, timeout_sec: float = 15.0) -> List[float]:
    """Возвращает до num_buckets чисел в диапазоне [0.0, 1.0] - пиковую
    амплитуду в каждом временном отрезке трека (по всей длине файла).
    Пустой список означает "волна недоступна" (формат не поддержан
    имеющимися средствами / файл не декодировался / файл пуст) -
    вызывающая сторона должна на этот случай рисовать плоскую
    линию-заглушку, а не падать.

    Пробует по очереди: stdlib `wave` (только настоящие .wav, без
    зависимостей) -> `miniaudio` (mp3/ogg-vorbis/flac/wav, один pip-пакет
    без системных зависимостей) -> `soundfile` (обёртка над libsndfile -
    дополнительно покрывает opus и нестандартные контейнеры). Останавливается
    на первом декодере, который успешно вернул непустой результат.

    timeout_sec больше не используется (не запускаем внешние процессы),
    параметр оставлен для обратной совместимости вызовов."""
    if not path or not os.path.isfile(path):
        return []

    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        result = _extract_peaks_wave(path, num_buckets)
        if result:
            return result
                                                                     
                                          

    result = _extract_peaks_miniaudio(path, num_buckets)
    if result:
        return result

    return _extract_peaks_soundfile(path, num_buckets)
