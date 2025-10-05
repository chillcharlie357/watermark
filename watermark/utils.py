from typing import Tuple
from PIL import Image
try:
    from PyQt6.QtGui import QImage, QPixmap
except Exception:
    QImage = None
    QPixmap = None


def _compute_nine_grid_position(image_size: Tuple[int, int], content_size: Tuple[int, int], position: str) -> Tuple[int, int]:
    """九宫格坐标计算（含四角、三中心、左右中）。"""
    img_w, img_h = image_size
    w, h = content_size
    margin = 10
    mapping = {
        "top-left": (margin, margin),
        "top-center": ((img_w - w) // 2, margin),
        "top-right": (img_w - w - margin, margin),
        "center-left": (margin, (img_h - h) // 2),
        "center": ((img_w - w) // 2, (img_h - h) // 2),
        "center-right": (img_w - w - margin, (img_h - h) // 2),
        "bottom-left": (margin, img_h - h - margin),
        "bottom-center": ((img_w - w) // 2, img_h - h - margin),
        "bottom-right": (img_w - w - margin, img_h - h - margin),
    }
    return mapping.get(position, mapping["bottom-right"])


def _pil_to_qpixmap(img: Image.Image) -> "QPixmap":
    """PIL.Image 转为 QPixmap，用 RGBA 并显式 bytesPerLine，避免颜色错位与撕裂。"""
    if QImage is None or QPixmap is None:
        raise RuntimeError("Qt bindings not available for QPixmap conversion")
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    bytes_per_line = img.width * 4
    qimage = QImage(data, img.width, img.height, bytes_per_line, QImage.Format.Format_RGBA8888)
    qimage = qimage.copy()
    return QPixmap.fromImage(qimage)