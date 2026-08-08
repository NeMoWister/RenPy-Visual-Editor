                       
"""
Рендер одного кадра перехода (см. core/transitions.py) между двумя уже
готовыми QPixmap - "старым" (снимок экрана до смены) и "новым" (снимок
после). Используется и в ui/scene_preview.py (редакторский предпросмотр), и
в ui/presentation_window.py (полноэкранная презентация) - единая логика,
чтобы поведение переходов было идентичным в обоих местах.
"""
import math
from typing import Optional, Tuple

try:
    import numpy as np
except ImportError:                                                        
    np = None

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPixmap, QColor, QImage

from core.transitions import TransitionSpec, TransitionKind


def punch_offset(spec: TransitionSpec, t: float) -> Tuple[float, float]:
    """Смещение экрана для vpunch/hpunch на момент t (сек. от начала
    эффекта) - быстрый удар-тряска и возврат, приближение к ATL
    Move(...)-тряске из стандартных переходов Ren'Py."""
    dur = spec.total_duration
    if t >= dur:
        return 0.0, 0.0
    progress = t / dur
                                                        
    damp = (1.0 - progress)
    wave = math.sin(progress * math.pi * 3) * damp
    amount = spec.punch_amount * wave
    if spec.punch_axis == "v":
        return 0.0, amount
    return amount, 0.0


_MASK_COMPUTE_MAX = 160                                                                    


def _mask_array(spec: TransitionSpec, mw: int, mh: int):
    """Строит градационную маску для встроенных blinds/squares в
    вычислительном разрешении (mw x mh) - numpy-массив float32 [0..1], либо
    (если numpy недоступен) обычный список списков той же формы."""
    if spec.mask_path == "__builtin_blinds__":
        stripe = max(2, mw // 8)
        if np is not None:
            xs = np.arange(mw)
            row = np.where((xs // stripe) % 2 == 0, 1.0, 0.16).astype(np.float32)
            return np.tile(row, (mh, 1))
        row = [1.0 if (x // stripe) % 2 == 0 else 0.16 for x in range(mw)]
        return [row[:] for _ in range(mh)]
    if spec.mask_path == "__builtin_squares__":
        cell = max(2, min(mw, mh) // 12)
        if np is not None:
            xs = (np.arange(mw) // cell).reshape(1, mw)
            ys = (np.arange(mh) // cell).reshape(mh, 1)
            v = ((xs * 7 + ys * 13) % 255) / 255.0
            return np.broadcast_to(v, (mh, mw)).astype(np.float32)
        return [[(((x // cell) * 7 + (y // cell) * 13) % 255) / 255.0 for x in range(mw)]
                for y in range(mh)]
    return None


_MASK_CACHE: dict = {}


def _compute_size(w: int, h: int) -> Tuple[int, int]:
    if max(w, h) <= _MASK_COMPUTE_MAX:
        return w, h
    scale = _MASK_COMPUTE_MAX / max(w, h)
    return max(1, int(w * scale)), max(1, int(h * scale))


def get_mask_array(spec: TransitionSpec, w: int, h: int, resolver=None):
    """resolver(mask_path) -> abs_path|None - разрешает путь маски (файл на
    диске) в момент кэширования. Кэш ключуется по (mask_path, mw, mh) и
    хранит уже готовый массив в СНИЖЕННОМ вычислительном разрешении (см.
    _MASK_COMPUTE_MAX) - этого достаточно для мягкого (с ramp) раскрытия и
    на порядки быстрее, чем гонять полноразмерную маску каждый кадр,
    особенно если numpy недоступен и приходится считать в чистом Python."""
    mw, mh = _compute_size(w, h)
    key = (spec.mask_path, mw, mh)
    if key in _MASK_CACHE:
        return _MASK_CACHE[key]
    if spec.mask_path in ("__builtin_blinds__", "__builtin_squares__"):
        arr = _mask_array(spec, mw, mh)
    else:
        abs_path = resolver(spec.mask_path) if resolver else spec.mask_path
        arr = None
        if abs_path:
            src = QImage(abs_path)
            if not src.isNull():
                gray = src.convertToFormat(QImage.Format.Format_Grayscale8).scaled(
                    mw, mh, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                arr = _qimage_gray_to_array(gray)
    _MASK_CACHE[key] = arr
    return arr


def _qimage_gray_to_array(img: QImage):
    w, h = img.width(), img.height()
    img = img.convertToFormat(QImage.Format.Format_Grayscale8)
    if np is not None:
        ptr = img.constBits()
        ptr.setsize(img.bytesPerLine() * h)
        buf = np.frombuffer(bytes(ptr), dtype=np.uint8).reshape(h, img.bytesPerLine())
        return (buf[:, :w].astype(np.float32)) / 255.0
    return [[img.pixelColor(x, y).lightnessF() for x in range(w)] for y in range(h)]


def _alpha_to_qimage_gray(mask, p: float, ramp: float, mw: int, mh: int) -> QImage:
    """alpha(pixel) = clamp((p - mask + ramp) / ramp, 0, 1) - тот же принцип
    порогового раскрытия по яркости маски, что и в Ren'Py ImageDissolve.

    ВАЖНО: результат используется как источник в CompositionMode_DestinationIn
    (см. render_transition_frame) - для этого нужен формат С альфа-каналом.
    Format_Grayscale8 альфа-канала не имеет, поэтому Qt считает такой источник
    полностью непрозрачным везде и DestinationIn не режет ничего - на экране
    всегда виден только новый кадр целиком, без самого перехода. Поэтому здесь
    именно Format_Alpha8 (формат, предназначенный Qt для масок прозрачности),
    а не Grayscale8."""
    if np is not None:
        alpha = np.clip((p - mask + ramp) / ramp, 0.0, 1.0)
        data = np.ascontiguousarray((alpha * 255.0).astype(np.uint8))
        img = QImage(data.data, mw, mh, mw, QImage.Format.Format_Alpha8)
        return img.copy()
    img = QImage(mw, mh, QImage.Format.Format_Alpha8)
    for y in range(mh):
        row = mask[y]
        for x in range(mw):
            a = max(0.0, min(1.0, (p - row[x] + ramp) / ramp))
            v = int(a * 255)
            img.setPixelColor(x, y, QColor(0, 0, 0, v))
    return img


def clear_mask_cache():
    _MASK_CACHE.clear()


def render_transition_frame(painter: QPainter, rect: QRect, old_pm: Optional[QPixmap],
                             new_pm: Optional[QPixmap], spec: TransitionSpec, t: float,
                             mask_resolver=None):
    """Рисует один кадр перехода в painter/rect на момент t (сек. от начала).
    old_pm/new_pm - снимки экрана "до" и "после" (тот же размер, что rect),
    могут быть None (тогда трактуются как чёрный кадр)."""
    w, h = rect.width(), rect.height()
    dur = spec.total_duration
    t = max(0.0, min(t, dur))
    p = progress = (t / dur) if dur > 0 else 1.0

    def draw(pm: Optional[QPixmap], opacity: float = 1.0, offset: Tuple[float, float] = (0.0, 0.0)):
        if opacity <= 0.001:
            return
        painter.save()
        painter.setOpacity(max(0.0, min(1.0, opacity)))
        if pm is not None:
            painter.drawPixmap(rect.x() + int(offset[0]), rect.y() + int(offset[1]), pm)
        else:
            painter.fillRect(QRect(rect.x() + int(offset[0]), rect.y() + int(offset[1]), w, h), QColor("#000000"))
        painter.restore()

    kind = spec.kind

    if kind == TransitionKind.DISSOLVE:
        draw(old_pm, 1.0)
        draw(new_pm, p)
        return

    if kind == TransitionKind.FADE:
        out_t, hold, in_t = spec.fade_out, spec.fade_hold, spec.fade_in
        color = QColor(spec.fade_color or "#000000")
        if t < out_t:
            frac = (t / out_t) if out_t > 0 else 1.0
            draw(old_pm, 1.0)
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, frac)))
            painter.fillRect(rect, color)
            painter.restore()
        elif t < out_t + hold:
            painter.fillRect(rect, color)
        else:
            frac = ((t - out_t - hold) / in_t) if in_t > 0 else 1.0
            draw(new_pm, 1.0)
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, 1.0 - frac)))
            painter.fillRect(rect, color)
            painter.restore()
        return

    if kind == TransitionKind.PIXELLATE:
        steps = max(1, spec.pixellate_steps)
        if p < 0.5:
            src, local = old_pm, p / 0.5
            block = max(1, int(local * (2 ** steps)))
        else:
            src, local = new_pm, 1.0 - (p - 0.5) / 0.5
            block = max(1, int(local * (2 ** steps)))
        if block <= 1 or src is None:
            draw(src if src is not None else new_pm, 1.0)
            return
        small_w = max(1, w // block)
        small_h = max(1, h // block)
        tiny = src.scaled(small_w, small_h, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.FastTransformation)
        blocky = tiny.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                              Qt.TransformationMode.FastTransformation)
        draw(blocky, 1.0)
        return

    if kind == TransitionKind.IMAGE_DISSOLVE:
        mask = get_mask_array(spec, w, h, resolver=mask_resolver)
        draw(old_pm, 1.0)
        if mask is None:
                                                              
            draw(new_pm, p)
            return
        mw, mh = _compute_size(w, h)
        ramp = max(1, spec.ramp) / 255.0
        alpha_small = _alpha_to_qimage_gray(mask, p, ramp, mw, mh)
        alpha_full = alpha_small if (mw, mh) == (w, h) else alpha_small.scaled(
            w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        composed = QPixmap(w, h)
        composed.fill(Qt.GlobalColor.transparent)
        cp = QPainter(composed)
        if new_pm is not None:
            cp.drawPixmap(0, 0, new_pm)
        cp.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        cp.drawImage(0, 0, alpha_full)
        cp.end()
        draw(composed, 1.0)
        return

    if kind == TransitionKind.WIPE:
        d = spec.direction
        if d == "left":
            edge = int(w * p)
            draw(new_pm, 1.0)
            if old_pm is not None:
                painter.save()
                painter.setClipRect(QRect(rect.x() + edge, rect.y(), w - edge, h))
                painter.drawPixmap(rect.x(), rect.y(), old_pm)
                painter.restore()
        elif d == "right":
            edge = int(w * p)
            draw(new_pm, 1.0)
            if old_pm is not None:
                painter.save()
                painter.setClipRect(QRect(rect.x(), rect.y(), w - edge, h))
                painter.drawPixmap(rect.x(), rect.y(), old_pm)
                painter.restore()
        elif d == "up":
            edge = int(h * p)
            draw(new_pm, 1.0)
            if old_pm is not None:
                painter.save()
                painter.setClipRect(QRect(rect.x(), rect.y() + edge, w, h - edge))
                painter.drawPixmap(rect.x(), rect.y(), old_pm)
                painter.restore()
        else:
            edge = int(h * p)
            draw(new_pm, 1.0)
            if old_pm is not None:
                painter.save()
                painter.setClipRect(QRect(rect.x(), rect.y(), w, h - edge))
                painter.drawPixmap(rect.x(), rect.y(), old_pm)
                painter.restore()
        return

    if kind == TransitionKind.PUSH:
        d = spec.direction
        if d == "left":
            off = int(w * p)
            draw(old_pm, 1.0, (-off, 0))
            draw(new_pm, 1.0, (w - off, 0))
        elif d == "right":
            off = int(w * p)
            draw(old_pm, 1.0, (off, 0))
            draw(new_pm, 1.0, (off - w, 0))
        elif d == "up":
            off = int(h * p)
            draw(old_pm, 1.0, (0, -off))
            draw(new_pm, 1.0, (0, h - off))
        else:
            off = int(h * p)
            draw(old_pm, 1.0, (0, off))
            draw(new_pm, 1.0, (0, off - h))
        return

                                                                          
    draw(new_pm if p >= 1.0 else old_pm, 1.0)
