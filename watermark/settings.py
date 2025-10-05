from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class WatermarkSettings:
    # 文本水印
    text_enabled: bool = True
    text: str = "Sample Watermark"
    font_size: int = 24
    color: Tuple[int, int, int] = (255, 255, 255)  # RGB
    text_alpha: int = 255  # 0-255
    stroke_enabled: bool = False
    stroke_color: Tuple[int, int, int] = (0, 0, 0)
    stroke_width: int = 0

    # 图片水印
    image_enabled: bool = False
    image_path: Optional[str] = None
    image_scale_percent: int = 50  # 1-500
    image_alpha: int = 255

    # 布局
    text_position: str = "bottom-right"
    text_custom_pos: Optional[Tuple[int, int]] = None
    image_position: str = "bottom-right"
    image_custom_pos: Optional[Tuple[int, int]] = None
    text_rotation_deg: float = 0.0
    image_rotation_deg: float = 0.0

    # 导出
    output_format: str = "JPEG"  # JPEG 或 PNG
    naming_rule: str = "suffix"  # original/prefix/suffix
    prefix: str = "wm_"
    suffix: str = "_watermarked"
    jpeg_quality: int = 90  # 0-100
    resize_percent: Optional[int] = None  # 按百分比缩放原图（可选）