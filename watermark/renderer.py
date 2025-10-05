import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from .utils import _compute_nine_grid_position


class WatermarkRenderer:
    """负责将文本/图片水印渲染到 PIL.Image 上。"""
    def __init__(self):
        pass

    def render(self, image: Image.Image, settings) -> Image.Image:
        # 保证 RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 可选缩放原图
        if getattr(settings, "resize_percent", None) and settings.resize_percent > 0:
            scale = settings.resize_percent / 100.0
            new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(image)

        # 清理上次记录
        self.last_text_rect = None
        self.last_image_rect = None

        # 绘制文本水印
        if getattr(settings, "text_enabled", False) and getattr(settings, "text", ""):
            self._draw_text(draw, image, settings)

        # 绘制图片水印
        if getattr(settings, "image_enabled", False) and getattr(settings, "image_path", None) and os.path.exists(settings.image_path):
            self._draw_image(image, settings)

        return image

    def _get_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", font_size)
            except Exception:
                return ImageFont.load_default()

    def _resolve_position(self, image: Image.Image, content_size: Tuple[int, int], custom_pos: Optional[Tuple[int,int]], preset_position: str) -> Tuple[int, int]:
        if custom_pos is not None:
            x = max(0, min(image.width - content_size[0], custom_pos[0]))
            y = max(0, min(image.height - content_size[1], custom_pos[1]))
            return (x, y)
        return _compute_nine_grid_position((image.width, image.height), content_size, preset_position)

    def _draw_text(self, draw: ImageDraw.ImageDraw, image: Image.Image, settings) -> None:
        font = self._get_font(settings.font_size)
        # 文本尺寸
        bbox = draw.textbbox((0, 0), settings.text, font=font, stroke_width=settings.stroke_width if settings.stroke_enabled else 0)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # 颜色+透明度
        r, g, b = settings.color
        fill = (r, g, b, settings.text_alpha)
        # 仅为文本创建最小透明层，避免旋转整个画布
        txt_img = Image.new("RGBA", (max(1, text_w), max(1, text_h)), (255, 255, 255, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        # 描边支持
        stroke_w = settings.stroke_width if settings.stroke_enabled else 0
        stroke_fill = (*settings.stroke_color, settings.text_alpha) if settings.stroke_enabled else None
        txt_draw.text((0, 0), settings.text, fill=fill, font=font, stroke_width=stroke_w, stroke_fill=stroke_fill)
        # 仅旋转文本层
        if settings.text_rotation_deg and abs(settings.text_rotation_deg) > 0.01:
            txt_img = txt_img.rotate(settings.text_rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)
        # 计算位置并叠加
        x, y = self._resolve_position(image, (txt_img.width, txt_img.height), settings.text_custom_pos, settings.text_position)
        image.paste(txt_img, (x, y), txt_img)
        # 记录文本水印最后矩形（原图坐标）
        self.last_text_rect = (x, y, txt_img.width, txt_img.height)

    def _draw_image(self, image: Image.Image, settings) -> None:
        try:
            wm = Image.open(settings.image_path)
            # 保持透明通道
            if wm.mode != "RGBA":
                wm = wm.convert("RGBA")
            # 按比例缩放
            scale = max(1, settings.image_scale_percent) / 100.0
            new_size = (max(1, int(wm.width * scale)), max(1, int(wm.height * scale)))
            wm = wm.resize(new_size, Image.Resampling.LANCZOS)
            # 应用整体透明度
            if settings.image_alpha < 255:
                alpha = wm.split()[3]
                alpha = alpha.point(lambda p: int(p * (settings.image_alpha / 255.0)))
                wm.putalpha(alpha)
            # 仅旋转水印图片
            if settings.image_rotation_deg and abs(settings.image_rotation_deg) > 0.01:
                wm = wm.rotate(settings.image_rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)
            # 位置
            x, y = self._resolve_position(image, (wm.width, wm.height), settings.image_custom_pos, settings.image_position)
            # 叠加
            image.paste(wm, (x, y), wm)
            # 记录图片水印最后矩形（原图坐标）
            self.last_image_rect = (x, y, wm.width, wm.height)
        except Exception as e:
            print(f"Error loading watermark image: {e}")