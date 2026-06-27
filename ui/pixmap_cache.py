
from typing import Dict, Optional, Tuple, List
from PyQt6.QtGui import QPixmap, QImageReader, QImage, QPainter
from PyQt6.QtCore import Qt, QSize

_full_cache: Dict[str, QPixmap] = {}
_scaled_cache: Dict[Tuple[str, int, int], QPixmap] = {}
_composite_cache: Dict[tuple, QPixmap] = {}


def get_pixmap(abs_path: str) -> Optional[QPixmap]:
    if abs_path in _full_cache:
        cached = _full_cache[abs_path]
        return cached if not cached.isNull() else None
    pm = QPixmap(abs_path)
    _full_cache[abs_path] = pm
    return pm if not pm.isNull() else None


def get_scaled(abs_path: str, width: int, height: int,
               aspect_mode: Qt.AspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio) -> Optional[QPixmap]:
    key = (abs_path, width, height)
    if key in _scaled_cache:
        return _scaled_cache[key]

    if abs_path in _full_cache:
        base = _full_cache[abs_path]
        if base.isNull():
            return None
        scaled = base.scaled(width, height, aspect_mode, Qt.TransformationMode.SmoothTransformation)
        _scaled_cache[key] = scaled
        return scaled

    scaled = _read_scaled_from_disk(abs_path, width, height, aspect_mode)
    if scaled is not None:
        _scaled_cache[key] = scaled
    return scaled


def _read_scaled_from_disk(abs_path: str, width: int, height: int,
                            aspect_mode: Qt.AspectRatioMode) -> Optional[QPixmap]:
    reader = QImageReader(abs_path)
    if not reader.canRead():
        return None
    src_size = reader.size()
    if src_size.isValid() and src_size.width() > 0 and src_size.height() > 0:
        if aspect_mode == Qt.AspectRatioMode.KeepAspectRatio:
            target = src_size.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        elif aspect_mode == Qt.AspectRatioMode.KeepAspectRatioByExpanding:
            target = src_size.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        else:
            target = QSize(width, height)
        reader.setScaledSize(target)
    image = reader.read()
    if image.isNull():
        return None
    return QPixmap.fromImage(image)


def get_composite(layer_paths_with_offsets: List[Tuple[str, int, int]], canvas_w: int, canvas_h: int,
                   target_w: Optional[int] = None, target_h: Optional[int] = None) -> Optional[QPixmap]:
    key = (tuple(layer_paths_with_offsets), canvas_w, canvas_h, target_w, target_h)
    if key in _composite_cache:
        return _composite_cache[key]

    canvas = QImage(canvas_w, canvas_h, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    any_drawn = False
    for abs_path, ox, oy in layer_paths_with_offsets:
        pm = get_pixmap(abs_path)
        if pm is None:
            continue
        painter.drawPixmap(ox, oy, pm)
        any_drawn = True
    painter.end()

    if not any_drawn:
        return None

    result = QPixmap.fromImage(canvas)
    if target_w and target_h:
        result = result.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
    _composite_cache[key] = result
    return result


def invalidate(abs_path: Optional[str] = None):
    global _full_cache, _scaled_cache, _composite_cache
    if abs_path is None:
        _full_cache = {}
        _scaled_cache = {}
        _composite_cache = {}
        return
    _full_cache.pop(abs_path, None)
    keys_to_drop = [k for k in _scaled_cache if k[0] == abs_path]
    for k in keys_to_drop:
        del _scaled_cache[k]
    composite_keys_to_drop = [
        k for k in _composite_cache
        if any(layer[0] == abs_path for layer in k[0])
    ]
    for k in composite_keys_to_drop:
        del _composite_cache[k]
