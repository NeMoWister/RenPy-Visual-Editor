                       
"""
Предпрослушивание музыки и звуков прямо в редакторе (без запуска Ren'Py).

Музыка стартует не с самого начала, а с 1/5 длительности трека — так
обычно слышен основной мотив, а не вступительная тишина/нарастание.
Звуковые эффекты всегда проигрываются с самого начала.

Один общий QMediaPlayer на всё приложение: запуск нового превью
автоматически останавливает предыдущее.
"""
from typing import Optional
from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPreviewPlayer(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.output = QAudioOutput()
        self.player.setAudioOutput(self.output)
        self._pending_start_fraction = 0.0
        self.player.durationChanged.connect(self._on_duration_changed)
        self._current_path: Optional[str] = None

    def play(self, path: str, start_fraction: float = 0.0):
        """Проигрывает файл с начала (start_fraction=0) или с указанной
        доли длительности (например, 0.2 — это 1/5 трека)."""
        if not path:
            return
        self.stop()
        self._pending_start_fraction = max(0.0, min(0.95, start_fraction))
        self._current_path = path
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def _on_duration_changed(self, duration_ms: int):
        if duration_ms > 0 and self._pending_start_fraction > 0:
            self.player.setPosition(int(duration_ms * self._pending_start_fraction))
            self._pending_start_fraction = 0.0                                          

    def stop(self):
        self.player.stop()
        self._current_path = None

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState


_shared_player: Optional[AudioPreviewPlayer] = None


def get_player() -> AudioPreviewPlayer:
    """Общий плеер на всё приложение (создаётся при первом обращении)."""
    global _shared_player
    if _shared_player is None:
        _shared_player = AudioPreviewPlayer()
    return _shared_player
