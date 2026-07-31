"""
Виджет волны для точной расстановки fadein/fadeout у аудио-нод
(play_music / play_sound / play_ambience) - доработка "звукового" плеера,
который раньше умел только play/stop без какой-либо визуализации.

Пики волны считаются в фоновом QThread через core.audio_waveform.extract_peaks
(ffmpeg), чтобы не подвешивать интерфейс на время декодирования. Если ffmpeg
не найден - виджет всё равно полностью рабочий (плоская линия вместо волны,
маркеры fadein/fadeout и перемотка кликом работают как обычно), просто без
самой картинки волны.
"""
from typing import List, Optional

from PyQt6.QtCore import Qt, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient
from PyQt6.QtWidgets import QWidget

from core.audio_waveform import extract_peaks, ffmpeg_available

NUM_BUCKETS = 400
HANDLE_HIT_PX = 7


def _fmt_time(ms: int) -> str:
    total = max(0, int(ms // 1000))
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


class _WaveformLoader(QThread):
    loaded = pyqtSignal(str, list)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        peaks = extract_peaks(self.path, NUM_BUCKETS)
        self.loaded.emit(self.path, peaks)


class WaveformWidget(QWidget):
    fadein_changed = pyqtSignal(float)                                
    fadeout_changed = pyqtSignal(float)                                
    seek_requested = pyqtSignal(float)                        

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)
        self.setMouseTracking(True)
        self._path: str = ""
        self._peaks: List[float] = []
        self._duration_ms: int = 0
        self._fadein_ms: int = 0
        self._fadeout_ms: int = 0
        self._position_ms: int = 0
        self._is_playing: bool = False
        self._dragging: Optional[str] = None                                 
        self._loader: Optional[_WaveformLoader] = None
        self._no_ffmpeg = not ffmpeg_available()

                            
    def set_audio(self, path: str, duration_ms: int = 0):
        self._path = path or ""
        self._peaks = []
        self._duration_ms = max(0, duration_ms)
        self._position_ms = 0
        self.update()
        if not self._path:
            return
        self._loader = _WaveformLoader(self._path, self)
        self._loader.loaded.connect(self._on_peaks_loaded)
        self._loader.start()

    def _on_peaks_loaded(self, path: str, peaks: list):
        if path != self._path:
            return                                     
        self._peaks = peaks
        self.update()

    def set_duration_ms(self, ms: int):
        if ms and ms > 0:
            self._duration_ms = ms
            self.update()

    def set_fades(self, fadein_sec: float, fadeout_sec: float):
        """Программная установка (например, из спинбоксов) - без сигналов обратно."""
        self._fadein_ms = max(0, int(round((fadein_sec or 0) * 1000)))
        self._fadeout_ms = max(0, int(round((fadeout_sec or 0) * 1000)))
        self.update()

    def set_position_ms(self, ms: int):
        self._position_ms = max(0, ms)
        self.update()

    def set_playing(self, playing: bool):
        self._is_playing = playing
        self.update()

                                        
    def _x_for_ms(self, ms: int) -> float:
        if self._duration_ms <= 0:
            return 0.0
        w = self.width()
        return max(0.0, min(w, (ms / self._duration_ms) * w))

    def _ms_for_x(self, x: float) -> int:
        if self._duration_ms <= 0:
            return 0
        w = max(1, self.width())
        frac = max(0.0, min(1.0, x / w))
        return int(frac * self._duration_ms)

    def _fadein_x(self) -> float:
        return self._x_for_ms(self._fadein_ms)

    def _fadeout_x(self) -> float:
        return self._x_for_ms(max(0, self._duration_ms - self._fadeout_ms))

                     
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        mid = h / 2

        p.fillRect(self.rect(), QColor("#1b1b1b"))

        if self._duration_ms <= 0:
            p.setPen(QColor("#666"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Выберите файл, чтобы увидеть волну")
            p.end()
            return

                                                              
        if self._peaks:
            bar_w = max(1.0, w / len(self._peaks))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#4a90d9"))
            for i, peak in enumerate(self._peaks):
                bh = max(1.0, peak * (h - 10))
                x = i * bar_w
                p.drawRect(QRectF(x, mid - bh / 2, max(1.0, bar_w - 1), bh))
        else:
            p.setPen(QColor("#3a3a3a"))
            p.drawLine(0, int(mid), w, int(mid))
            if self._no_ffmpeg:
                p.setPen(QColor("#666"))
                p.drawText(self.rect().adjusted(4, 0, -4, 0),
                           Qt.AlignmentFlag.AlignCenter,
                           "Волна недоступна (не найден ffmpeg) - перемотка и fade всё равно работают")

                                                       
        fi_x = self._fadein_x()
        if fi_x > 0:
            grad = QLinearGradient(0, 0, fi_x, 0)
            grad.setColorAt(0.0, QColor(255, 140, 61, 130))
            grad.setColorAt(1.0, QColor(255, 140, 61, 0))
            p.fillRect(QRectF(0, 0, fi_x, h), grad)

        fo_x = self._fadeout_x()
        if fo_x < w:
            grad = QLinearGradient(fo_x, 0, w, 0)
            grad.setColorAt(0.0, QColor(90, 160, 255, 0))
            grad.setColorAt(1.0, QColor(90, 160, 255, 130))
            p.fillRect(QRectF(fo_x, 0, w - fo_x, h), grad)

                
        pen = QPen(QColor("#ff8c3d"))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawLine(int(fi_x), 0, int(fi_x), h)

        pen = QPen(QColor("#5aa0ff"))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawLine(int(fo_x), 0, int(fo_x), h)

                  
        px = self._x_for_ms(min(self._position_ms, self._duration_ms))
        pen = QPen(QColor("#6fd68f" if self._is_playing else "#aaaaaa"))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(int(px), 0, int(px), h)

                                       
        p.setPen(QColor("#999"))
        p.drawText(4, h - 4, _fmt_time(0))
        p.drawText(w - 34, h - 4, _fmt_time(self._duration_ms))
        p.setPen(QColor("#ff8c3d"))
        p.drawText(max(2, int(fi_x) + 3), 12, f"in {self._fadein_ms/1000:.1f}s")
        p.setPen(QColor("#5aa0ff"))
        fo_label = f"out {self._fadeout_ms/1000:.1f}s"
        p.drawText(min(w - 60, int(fo_x) + 3), 12, fo_label)

        p.end()

                                
    def _near(self, x: float, target_x: float) -> bool:
        return abs(x - target_x) <= HANDLE_HIT_PX

    def mousePressEvent(self, event):
        if self._duration_ms <= 0:
            return
        x = event.position().x()
        if self._near(x, self._fadein_x()):
            self._dragging = "fadein"
        elif self._near(x, self._fadeout_x()):
            self._dragging = "fadeout"
        else:
            self._dragging = None
            self.seek_requested.emit(self._ms_for_x(x) / 1000.0)

    def mouseMoveEvent(self, event):
        if self._duration_ms <= 0 or self._dragging is None:
            return
        x = event.position().x()
        ms = self._ms_for_x(x)
        if self._dragging == "fadein":
            self._fadein_ms = max(0, min(ms, self._duration_ms))
            self.fadein_changed.emit(self._fadein_ms / 1000.0)
        else:
            fadeout_ms = max(0, min(self._duration_ms - ms, self._duration_ms))
            self._fadeout_ms = fadeout_ms
            self.fadeout_changed.emit(self._fadeout_ms / 1000.0)
        self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = None
