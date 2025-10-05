from __future__ import annotations
import os
import argparse
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import glob
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

# 可选：PyQt6 导入（GUI 模式需要）
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QApplication, QWidget, QHBoxLayout, QVBoxLayout,
        QListWidget, QListWidgetItem, QPushButton, QCheckBox, QLineEdit,
        QSpinBox, QSlider, QGroupBox, QLabel, QComboBox, QFileDialog, QScrollArea,
        QMessageBox, QColorDialog
    )
    from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QFont, QColor, QPen, QPainterPath, QFontMetrics
    from PyQt6.QtCore import QSize, QPoint, Qt, QTimer
    PYQT_AVAILABLE = True
except Exception:
    PYQT_AVAILABLE = False
    # 允许无 PyQt6 时导入 CLI 模块：提供最简基类占位
    class QMainWindow:
        pass


def get_exif_date(image_path):
    """从图片的EXIF信息中提取拍摄日期"""
    try:
        with Image.open(image_path) as image:
            exifdata = image.getexif()
            
            # 查找日期相关的EXIF标签
            date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
            
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                if tag in date_tags:
                    date_str = exifdata[tag_id]
                    if date_str:
                        # 解析日期字符串 (格式: YYYY:MM:DD HH:MM:SS)
                        try:
                            date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                            return date_obj.strftime("%B %d, %Y")
                        except ValueError:
                            continue
            
            # 如果没有找到EXIF日期，使用文件修改时间
            file_time = os.path.getmtime(image_path)
            date_obj = datetime.fromtimestamp(file_time)
            return date_obj.strftime("%B %d, %Y")
            
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
        # 使用文件修改时间作为备选
        try:
            file_time = os.path.getmtime(image_path)
            date_obj = datetime.fromtimestamp(file_time)
            return date_obj.strftime("%B %d, %Y")
        except:
            return "Unknown Date"


def get_position_coordinates(image_size, text_size, position):
    """根据位置参数计算文本坐标"""
    img_width, img_height = image_size
    text_width, text_height = text_size
    
    if position == "top-left":
        return (10, 10)
    elif position == "top-right":
        return (img_width - text_width - 10, 10)
    elif position == "bottom-left":
        return (10, img_height - text_height - 10)
    elif position == "bottom-right":
        return (img_width - text_width - 10, img_height - text_height - 10)
    elif position == "center":
        return ((img_width - text_width) // 2, (img_height - text_height) // 2)
    else:
        # 默认右下角
        return (img_width - text_width - 10, img_height - text_height - 10)


def add_watermark(image_path, output_path, watermark_text, font_size=24, color="white", position="bottom-right"):
    """为图片添加水印"""
    try:
        # 打开图片
        with Image.open(image_path) as image:
            # 转换为RGB模式（如果是RGBA或其他模式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 创建绘图对象
            draw = ImageDraw.Draw(image)
            
            # 尝试加载字体，如果失败则使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", font_size)  # 中文字体
                except:
                    font = ImageFont.load_default()
            
            # 获取文本尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 计算文本位置
            x, y = get_position_coordinates(image.size, (text_width, text_height), position)
            
            # 绘制文本
            draw.text((x, y), watermark_text, fill=color, font=font)
            
            # 保存图片
            image.save(output_path, "JPEG", quality=95)
            print(f"Saved watermarked image: {output_path}")
            
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")


def process_images(input_path, font_size=24, color="white", position="bottom-right"):
    """处理指定路径下的所有图片"""
    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"Error: Path {input_path} does not exist")
        return
    
    # 支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
    
    # 查找所有图片文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_path, ext)))
        image_files.extend(glob.glob(os.path.join(input_path, ext.upper())))
    
    if not image_files:
        print(f"No image files found in {input_path}")
        return
    
    # 创建输出目录
    base_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
    dir_name = os.path.basename(base_dir)
    output_dir = os.path.join(base_dir, f"{dir_name}_watermark")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # 处理每张图片
    for image_file in image_files:
        # 获取EXIF日期作为水印文本
        watermark_text = get_exif_date(image_file)
        
        # 生成输出文件名
        filename = os.path.basename(image_file)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_watermark.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing image: {filename} -> Watermark: {watermark_text}")
        add_watermark(image_file, output_path, watermark_text, font_size, color, position)


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


def main():
    parser = argparse.ArgumentParser(description="Image Watermark Tool")
    parser.add_argument("path", help="Image file path or directory path containing images")
    parser.add_argument("-s", "--size", type=int, default=24, help="Font size (default: 24)")
    parser.add_argument("-c", "--color", default="white", help="Watermark color (default: white)")
    parser.add_argument("-p", "--position", 
                       choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                       default="bottom-right", 
                       help="Watermark position (default: bottom-right)")
    
    args = parser.parse_args()
    
    print("=== Image Watermark Tool ===")
    print(f"Input path: {args.path}")
    print(f"Font size: {args.size}")
    print(f"Watermark color: {args.color}")
    print(f"Watermark position: {args.position}")
    print("-" * 30)
    
    process_images(args.path, args.size, args.color, args.position)
    
    print("Processing completed!")


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
    # 文本与图片分别的预设位置与自定义坐标
    text_position: str = "bottom-right"
    text_custom_pos: Optional[Tuple[int, int]] = None
    image_position: str = "bottom-right"
    image_custom_pos: Optional[Tuple[int, int]] = None
    rotation_deg: float = 0.0  # 可选

    # 导出
    output_format: str = "JPEG"  # JPEG 或 PNG
    naming_rule: str = "suffix"  # original/prefix/suffix
    prefix: str = "wm_"
    suffix: str = "_watermarked"
    jpeg_quality: int = 90  # 0-100
    resize_percent: Optional[int] = None  # 按百分比缩放原图（可选）


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    """PIL.Image 转为 QPixmap，用 RGBA 并显式 bytesPerLine，避免颜色错位与撕裂。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    bytes_per_line = img.width * 4
    qimage = QImage(data, img.width, img.height, bytes_per_line, QImage.Format.Format_RGBA8888)
    # 复制一份以与原始内存分离，避免临时缓冲释放导致显示异常
    qimage = qimage.copy()
    return QPixmap.fromImage(qimage)


class WatermarkRenderer:
    """负责将文本/图片水印渲染到 PIL.Image 上。"""
    def __init__(self):
        pass

    def render(self, image: Image.Image, settings: WatermarkSettings) -> Image.Image:
        # 保证 RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 可选缩放原图
        if settings.resize_percent and settings.resize_percent > 0:
            scale = settings.resize_percent / 100.0
            new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(image)

        # 清理上次记录
        self.last_text_rect = None
        self.last_image_rect = None

        # 绘制文本水印
        if settings.text_enabled and settings.text:
            self._draw_text(draw, image, settings)

        # 绘制图片水印
        if settings.image_enabled and settings.image_path and os.path.exists(settings.image_path):
            self._draw_image(image, settings)

        return image

    def _get_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", font_size)
            except:
                return ImageFont.load_default()

    def _resolve_position(self, image: Image.Image, content_size: Tuple[int, int], custom_pos: Optional[Tuple[int,int]], preset_position: str) -> Tuple[int, int]:
        if custom_pos is not None:
            x = max(0, min(image.width - content_size[0], custom_pos[0]))
            y = max(0, min(image.height - content_size[1], custom_pos[1]))
            return (x, y)
        return _compute_nine_grid_position((image.width, image.height), content_size, preset_position)

    def _draw_text(self, draw: ImageDraw.ImageDraw, image: Image.Image, settings: WatermarkSettings) -> None:
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
        if settings.rotation_deg and abs(settings.rotation_deg) > 0.01:
            txt_img = txt_img.rotate(settings.rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)
        # 计算位置并叠加
        x, y = self._resolve_position(image, (txt_img.width, txt_img.height), settings.text_custom_pos, settings.text_position)
        image.paste(txt_img, (x, y), txt_img)
        # 记录文本水印最后矩形（原图坐标）
        self.last_text_rect = (x, y, txt_img.width, txt_img.height)

    def _draw_image(self, image: Image.Image, settings: WatermarkSettings) -> None:
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
            if settings.rotation_deg and abs(settings.rotation_deg) > 0.01:
                wm = wm.rotate(settings.rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)
            # 位置
            x, y = self._resolve_position(image, (wm.width, wm.height), settings.image_custom_pos, settings.image_position)
            # 叠加
            image.paste(wm, (x, y), wm)
            # 记录图片水印最后矩形（原图坐标）
            self.last_image_rect = (x, y, wm.width, wm.height)
        except Exception as e:
            print(f"Error loading watermark image: {e}")


class MainWindow(QMainWindow):
    """PyQt6 GUI 主窗口：负责导入图片列表、预览与控制面板、批量导出。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Tool")
        self.resize(1200, 800)
        self.settings = WatermarkSettings()
        self.renderer = WatermarkRenderer()
        self.image_paths: List[str] = []
        self.current_index: int = -1
        self.output_dir: Optional[str] = None
        self._dragging = False
        self._drag_offset = QPoint(0, 0)
        # 预览优化：缓存当前图片与节流计时器
        self._base_image: Optional[Image.Image] = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(16)  # ~60 FPS
        self._preview_timer.timeout.connect(self._do_update_preview)
        # 拖拽覆盖层：在预览上直接绘制水印
        self._drag_base_pixmap: Optional[QPixmap] = None
        self._drag_img_qpixmap_cache: Optional[QPixmap] = None
        # 显示/记录当前模板路径
        self._current_template_path: Optional[str] = None

        self._init_ui()
        self.setAcceptDrops(True)

    # UI 构建（单一职责：组装控件与布局）
    def _init_ui(self):
        root = QWidget()
        layout = QHBoxLayout(root)
        self.setCentralWidget(root)

        # 左侧：图片列表
        left_box = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(120, 90))
        self.list_widget.currentRowChanged.connect(self._on_image_selected)
        left_box.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_add_files = QPushButton("添加图片")
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.clicked.connect(self._clear_list)
        btn_row.addWidget(self.btn_add_files)
        btn_row.addWidget(self.btn_add_folder)
        btn_row.addWidget(self.btn_clear)
        left_box.addLayout(btn_row)

        layout.addLayout(left_box, 3)

        # 中间：预览
        center_box = QVBoxLayout()
        self.preview_label = QLabel("预览区")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background:#333;color:#ccc")
        center_box.addWidget(self.preview_label, 10)

        # 预览内部状态：用于拖拽映射
        self._preview_scale_x = 1.0
        self._preview_scale_y = 1.0
        self._preview_offset_x = 0
        self._preview_offset_y = 0
        self._drag_target = None  # 'text' | 'image' | None
        self._drag_start_pos_img = (0, 0)  # 原图坐标中的起始左上角

        layout.addLayout(center_box, 7)

        # 右侧：控制面板
        right_box = QVBoxLayout()

        # 文本水印设置
        grp_text = QGroupBox("文本水印")
        vb_text = QVBoxLayout(grp_text)
        self.chk_text_enable = QCheckBox("启用文本水印")
        self.chk_text_enable.setChecked(self.settings.text_enabled)
        self.chk_text_enable.stateChanged.connect(lambda _: self._on_text_enable_toggled())
        self.btn_del_text = QPushButton("删除文本水印")
        self.btn_del_text.clicked.connect(self._delete_text)
        self.txt_input = QLineEdit(self.settings.text)
        self.txt_input.textChanged.connect(self._on_text_changed)
        self.sp_font = QSpinBox(); self.sp_font.setRange(8, 300); self.sp_font.setValue(self.settings.font_size)
        self.sp_font.valueChanged.connect(self._on_font_changed)
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self._choose_color)
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal); self.slider_alpha.setRange(0, 255); self.slider_alpha.setValue(self.settings.text_alpha)
        self.slider_alpha.valueChanged.connect(self._on_alpha_changed)
        self.chk_stroke = QCheckBox("描边")
        self.chk_stroke.stateChanged.connect(lambda _: self._on_stroke_toggle())
        self.sp_stroke = QSpinBox(); self.sp_stroke.setRange(0, 10); self.sp_stroke.setValue(self.settings.stroke_width); self.sp_stroke.valueChanged.connect(self._on_stroke_width_changed)
        vb_text.addWidget(self.chk_text_enable)
        vb_text.addWidget(self.btn_del_text)
        # 文本位置与拖拽
        pos_text_row = QHBoxLayout()
        pos_text_row.addWidget(QLabel("文本位置"))
        self.pos_text_combo = QComboBox()
        self.pos_text_combo.addItems([
            "top-left","top-center","top-right",
            "center-left","center","center-right",
            "bottom-left","bottom-center","bottom-right"
        ])
        self.pos_text_combo.setCurrentText(self.settings.text_position)
        self.pos_text_combo.currentTextChanged.connect(self._on_text_position_changed)
        self.chk_text_drag = QCheckBox("拖拽文本")
        self.chk_text_drag.setChecked(False)
        pos_text_row.addWidget(self.pos_text_combo)
        pos_text_row.addWidget(self.chk_text_drag)
        vb_text.addLayout(pos_text_row)
        vb_text.addWidget(QLabel("文本内容")); vb_text.addWidget(self.txt_input)
        vb_text.addWidget(QLabel("字号")); vb_text.addWidget(self.sp_font)
        vb_text.addWidget(self.btn_color)
        vb_text.addWidget(QLabel("不透明度")); vb_text.addWidget(self.slider_alpha)
        vb_text.addWidget(self.chk_stroke); vb_text.addWidget(QLabel("描边宽度")); vb_text.addWidget(self.sp_stroke)
        right_box.addWidget(grp_text)

        # 图片水印设置
        grp_img = QGroupBox("图片水印")
        vb_img = QVBoxLayout(grp_img)
        self.chk_img_enable = QCheckBox("启用图片水印")
        self.chk_img_enable.setChecked(self.settings.image_enabled)
        self.chk_img_enable.stateChanged.connect(lambda _: self._on_img_enable_toggled())
        self.btn_choose_img = QPushButton("选择 PNG")
        self.btn_choose_img.clicked.connect(self._choose_image)
        self.btn_del_img = QPushButton("删除图片水印")
        self.btn_del_img.clicked.connect(self._delete_image)
        self.sp_img_scale = QSpinBox(); self.sp_img_scale.setRange(1, 500); self.sp_img_scale.setValue(self.settings.image_scale_percent)
        self.sp_img_scale.valueChanged.connect(self._on_img_scale_changed)
        self.slider_img_alpha = QSlider(Qt.Orientation.Horizontal); self.slider_img_alpha.setRange(0, 255); self.slider_img_alpha.setValue(self.settings.image_alpha)
        self.slider_img_alpha.valueChanged.connect(self._on_img_alpha_changed)
        vb_img.addWidget(self.chk_img_enable)
        vb_img.addWidget(self.btn_choose_img)
        vb_img.addWidget(self.btn_del_img)
        # 图片位置与拖拽
        pos_img_row = QHBoxLayout()
        pos_img_row.addWidget(QLabel("图片位置"))
        self.pos_img_combo = QComboBox()
        self.pos_img_combo.addItems([
            "top-left","top-center","top-right",
            "center-left","center","center-right",
            "bottom-left","bottom-center","bottom-right"
        ])
        self.pos_img_combo.setCurrentText(self.settings.image_position)
        self.pos_img_combo.currentTextChanged.connect(self._on_img_position_changed)
        self.chk_img_drag_ctrl = QCheckBox("拖拽图片")
        self.chk_img_drag_ctrl.setChecked(False)
        pos_img_row.addWidget(self.pos_img_combo)
        pos_img_row.addWidget(self.chk_img_drag_ctrl)
        vb_img.addLayout(pos_img_row)
        vb_img.addWidget(QLabel("缩放(%)")); vb_img.addWidget(self.sp_img_scale)
        vb_img.addWidget(QLabel("不透明度")); vb_img.addWidget(self.slider_img_alpha)
        right_box.addWidget(grp_img)

        # 导出设置
        grp_out = QGroupBox("导出设置")
        vb_out = QVBoxLayout(grp_out)
        self.btn_choose_out = QPushButton("选择输出目录")
        self.btn_choose_out.clicked.connect(self._choose_output_dir)
        self.cmb_format = QComboBox(); self.cmb_format.addItems(["JPEG", "PNG"]); self.cmb_format.setCurrentText(self.settings.output_format)
        self.cmb_format.currentTextChanged.connect(lambda v: self._set_output_format(v))
        self.cmb_naming = QComboBox(); self.cmb_naming.addItems(["original", "prefix", "suffix"]); self.cmb_naming.setCurrentText(self.settings.naming_rule)
        self.cmb_naming.currentTextChanged.connect(lambda v: self._set_naming_rule(v))
        self.ed_prefix = QLineEdit(self.settings.prefix)
        self.ed_prefix.textChanged.connect(lambda v: self._set_prefix(v))
        self.ed_suffix = QLineEdit(self.settings.suffix)
        self.ed_suffix.textChanged.connect(lambda v: self._set_suffix(v))
        self.slider_quality = QSlider(Qt.Orientation.Horizontal); self.slider_quality.setRange(0, 100); self.slider_quality.setValue(self.settings.jpeg_quality)
        self.slider_quality.valueChanged.connect(lambda v: self._set_quality(v))
        self.sp_resize = QSpinBox(); self.sp_resize.setRange(1, 500); self.sp_resize.setValue(self.settings.resize_percent or 100)
        self.chk_resize = QCheckBox("按百分比缩放原图")
        self.chk_resize.stateChanged.connect(lambda _: self._toggle_resize())
        self.lbl_quality = QLabel("JPEG质量")
        vb_out.addWidget(self.btn_choose_out)
        vb_out.addWidget(QLabel("输出格式")); vb_out.addWidget(self.cmb_format)
        vb_out.addWidget(QLabel("命名规则")); vb_out.addWidget(self.cmb_naming)
        vb_out.addWidget(QLabel("前缀")); vb_out.addWidget(self.ed_prefix)
        vb_out.addWidget(QLabel("后缀")); vb_out.addWidget(self.ed_suffix)
        vb_out.addWidget(self.lbl_quality); vb_out.addWidget(self.slider_quality)
        vb_out.addWidget(self.chk_resize); vb_out.addWidget(QLabel("缩放(%)")); vb_out.addWidget(self.sp_resize)
        right_box.addWidget(grp_out)

        # 模板管理
        grp_tpl = QGroupBox("模板与设置")
        vb_tpl = QVBoxLayout(grp_tpl)
        # 当前模板名显示
        self.lbl_tpl_name = QLabel("当前模板：未选择")
        vb_tpl.addWidget(self.lbl_tpl_name)
        self.btn_save_tpl = QPushButton("保存模板")
        self.btn_save_tpl.clicked.connect(self._save_template)
        self.btn_load_tpl = QPushButton("加载模板")
        self.btn_load_tpl.clicked.connect(self._load_template)
        # 新增：删除模板
        self.btn_del_tpl = QPushButton("删除模板")
        self.btn_del_tpl.clicked.connect(self._delete_template)
        vb_tpl.addWidget(self.btn_save_tpl)
        vb_tpl.addWidget(self.btn_load_tpl)
        vb_tpl.addWidget(self.btn_del_tpl)
        right_box.addWidget(grp_tpl)

        # 导出按钮
        self.btn_export = QPushButton("批量导出")
        self.btn_export.clicked.connect(self._export_all)
        right_box.addWidget(self.btn_export)
        right_box.addStretch(1)

        # 使用滚动区域包裹右侧控制面板，提供垂直滚动条
        right_panel = QWidget()
        right_panel.setLayout(right_box)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel)
        layout.addWidget(right_scroll, 4)

        # 初始状态：根据启用开关禁用相关控件、根据格式隐藏质量控件、根据缩放选项禁用输入
        self._update_text_controls_enabled()
        self._update_img_controls_enabled()
        self._update_output_format_controls()
        self.sp_resize.setEnabled(self.chk_resize.isChecked())

    # 文件导入相关（单一职责：管理图片列表）
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)")
        self._append_images(paths)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder:
            exts = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]
            files = []
            for root, _, names in os.walk(folder):
                for n in names:
                    if os.path.splitext(n)[1].lower() in exts:
                        files.append(os.path.join(root, n))
            self._append_images(files)

    def _append_images(self, paths: List[str]):
        added = 0
        for p in paths:
            if not os.path.exists(p):
                continue
            ext = os.path.splitext(p)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]:
                continue
            if p not in self.image_paths:
                self.image_paths.append(p)
                item = QListWidgetItem(os.path.basename(p))
                # 缩略图
                try:
                    with Image.open(p) as im:
                        im.thumbnail((160, 120), Image.Resampling.LANCZOS)
                        # 使用 QIcon 设置缩略图图标
                        item.setIcon(QIcon(QPixmap.fromImage(QImage(
                            im.tobytes("raw", im.mode if im.mode in ("RGB","RGBA") else "RGB"),
                            im.width,
                            im.height,
                            QImage.Format.Format_RGB888 if im.mode=="RGB" else QImage.Format.Format_RGBA8888
                        ))))
                except Exception:
                    pass
                self.list_widget.addItem(item)
                added += 1
        if added and self.current_index == -1:
            self.list_widget.setCurrentRow(0)

    def _clear_list(self):
        self.image_paths.clear()
        self.list_widget.clear()
        self.current_index = -1
        self.preview_label.setPixmap(QPixmap())

    def _on_image_selected(self, idx: int):
        self.current_index = idx
        # 选择图片时预加载到内存，减少每次渲染的文件IO
        try:
            if 0 <= idx < len(self.image_paths):
                path = self.image_paths[idx]
                with Image.open(path) as im:
                    self._base_image = im.copy()
        except Exception:
            self._base_image = None
        self._do_update_preview()

    # 拖拽导入
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        paths = [u.toLocalFile() for u in urls]
        folders = []
        files = []
        for p in paths:
            if os.path.isdir(p):
                folders.append(p)
            else:
                files.append(p)
        self._append_images(files)
        for folder in folders:
            exts = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]
            collected = []
            for root, _, names in os.walk(folder):
                for n in names:
                    if os.path.splitext(n)[1].lower() in exts:
                        collected.append(os.path.join(root, n))
            self._append_images(collected)

    # 预览更新：拖拽期间节流，非拖拽即时
    def _update_preview(self):
        if self._dragging:
            # 拖拽时合并高频事件，约 60FPS 更新
            if not self._preview_timer.isActive():
                self._preview_timer.start()
            return
        # 非拖拽时立即渲染
        self._do_update_preview()

    # 实际渲染逻辑（渲染当前图片与设置）
    def _do_update_preview(self):
        if self.current_index < 0 or self.current_index >= len(self.image_paths):
            return
        path = self.image_paths[self.current_index]
        try:
            # 使用缓存的原图，避免每次打开文件造成卡顿
            base = None
            if self._base_image is not None:
                base = self._base_image.copy()
            else:
                with Image.open(path) as im:
                    base = im.copy()
                    self._base_image = base.copy()

            out = self.renderer.render(base, self.settings)
            # 为避免预览过大，缩放到窗口大小
            label_w = self.preview_label.width()
            label_h = self.preview_label.height()
            if out.width > 0 and out.height > 0:
                pre_w, pre_h = out.width, out.height
                scale_w = label_w - 20
                scale_h = label_h - 20
                if scale_w > 50 and scale_h > 50:
                    # 拖拽时使用较快的插值以提升实时性
                    resample = Image.Resampling.BILINEAR if self._dragging else Image.Resampling.LANCZOS
                    out.thumbnail((scale_w, scale_h), resample)
                # 计算缩放与偏移用于命中测试
                self._preview_scale_x = (out.width / pre_w) if pre_w else 1.0
                self._preview_scale_y = (out.height / pre_h) if pre_h else 1.0
                self._preview_offset_x = max(0, (label_w - out.width) // 2)
                self._preview_offset_y = max(0, (label_h - out.height) // 2)
            self.preview_label.setPixmap(_pil_to_qpixmap(out))
        except Exception as e:
            print(f"Preview error: {e}")

    # 预设位置变更
    def _on_text_position_changed(self, v: str):
        self.settings.text_position = v
        self.settings.text_custom_pos = None
        self._update_preview()

    def _on_img_position_changed(self, v: str):
        self.settings.image_position = v
        self.settings.image_custom_pos = None
        self._update_preview()

    # 文本设置回调
    def _on_text_changed(self, v: str):
        self.settings.text = v
        self._update_preview()

    def _on_font_changed(self, v: int):
        self.settings.font_size = v
        self._update_preview()

    def _choose_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.settings.color = (c.red(), c.green(), c.blue())
            self._update_preview()

    def _on_alpha_changed(self, v: int):
        self.settings.text_alpha = v
        self._update_preview()

    def _on_stroke_toggle(self):
        self.settings.stroke_enabled = self.chk_stroke.isChecked()
        self._update_preview()

    def _on_stroke_width_changed(self, v: int):
        self.settings.stroke_width = v
        self._update_preview()

    def _on_text_enable_toggled(self):
        self.settings.text_enabled = self.chk_text_enable.isChecked()
        self._update_text_controls_enabled()
        self._update_preview()

    # 图片水印设置回调
    def _choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "PNG Images (*.png)")
        if path:
            self.settings.image_path = path
            self.settings.image_enabled = True
            self.chk_img_enable.setChecked(True)
            self._update_preview()

    def _on_img_enable_toggled(self):
        self.settings.image_enabled = self.chk_img_enable.isChecked()
        self._update_img_controls_enabled()
        self._update_preview()

    def _on_img_scale_changed(self, v: int):
        self.settings.image_scale_percent = v
        self._update_preview()

    def _on_img_alpha_changed(self, v: int):
        self.settings.image_alpha = v
        self._update_preview()

    # 导出设置回调
    def _choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if d:
            self.output_dir = d

    def _set_output_format(self, v: str):
        self.settings.output_format = v
        self._update_output_format_controls()
        self._update_preview()

    def _set_naming_rule(self, v: str):
        self.settings.naming_rule = v

    def _set_prefix(self, v: str):
        self.settings.prefix = v

    def _set_suffix(self, v: str):
        self.settings.suffix = v

    def _set_quality(self, v: int):
        self.settings.jpeg_quality = v

    def _toggle_resize(self):
        if self.chk_resize.isChecked():
            self.settings.resize_percent = self.sp_resize.value()
        else:
            self.settings.resize_percent = None
        self.sp_resize.setEnabled(self.chk_resize.isChecked())
        self._update_preview()

    # 预览区拖拽定位（单一职责：处理手动拖拽）
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.preview_label.underMouse():
            # 将鼠标位置映射到预览标签坐标
            pt = self.preview_label.mapFromGlobal(e.globalPosition().toPoint())
            x_in_label = pt.x() - self._preview_offset_x
            y_in_label = pt.y() - self._preview_offset_y
            # 命中文本或图片矩形（缩放后）
            hit_target = None
            def hit(rect):
                if not rect:
                    return False
                rx, ry, rw, rh = rect
                sx = int(rx * self._preview_scale_x)
                sy = int(ry * self._preview_scale_y)
                sw = int(rw * self._preview_scale_x)
                sh = int(rh * self._preview_scale_y)
                return 0 <= x_in_label - sx < sw and 0 <= y_in_label - sy < sh

            if self.chk_text_drag.isChecked() and hit(self.renderer.last_text_rect):
                hit_target = 'text'
            elif self.chk_img_drag_ctrl.isChecked() and hit(self.renderer.last_image_rect):
                hit_target = 'image'

            if hit_target:
                self._dragging = True
                self._drag_target = hit_target
                # 记录起始点（原图坐标）
                if hit_target == 'text' and self.renderer.last_text_rect:
                    self._drag_start_pos_img = (self.renderer.last_text_rect[0], self.renderer.last_text_rect[1])
                elif hit_target == 'image' and self.renderer.last_image_rect:
                    self._drag_start_pos_img = (self.renderer.last_image_rect[0], self.renderer.last_image_rect[1])
                # 记录按下的预览坐标
                self._drag_offset = pt
                # 准备拖拽覆盖层：生成无水印的预览底图
                try:
                    self._prepare_drag_base_preview()
                except Exception:
                    pass

    def mouseMoveEvent(self, e):
        if self._dragging and self.current_index >= 0 and self._drag_target:
            pt = self.preview_label.mapFromGlobal(e.globalPosition().toPoint())
            dx_label = pt.x() - self._drag_offset.x()
            dy_label = pt.y() - self._drag_offset.y()
            # 转换到原图坐标的增量
            dx_img = int(dx_label / (self._preview_scale_x or 1.0))
            dy_img = int(dy_label / (self._preview_scale_y or 1.0))
            start_x, start_y = self._drag_start_pos_img
            new_x = max(0, start_x + dx_img)
            new_y = max(0, start_y + dy_img)
            if self._drag_target == 'text':
                self.settings.text_custom_pos = (new_x, new_y)
            elif self._drag_target == 'image':
                self.settings.image_custom_pos = (new_x, new_y)
            # 拖拽中使用覆盖层快速刷新
            self._update_overlay_preview()

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_target = None
            # 拖拽结束，进行一次高质量整图渲染
            self._drag_base_pixmap = None
            self._drag_img_qpixmap_cache = None
            self._do_update_preview()

    # 生成无水印的预览底图（仅用于拖拽期间覆盖层绘制）
    def _prepare_drag_base_preview(self):
        if self.current_index < 0 or self.current_index >= len(self.image_paths):
            return
        path = self.image_paths[self.current_index]
        # 使用缓存原图
        base = None
        if self._base_image is not None:
            base = self._base_image.copy()
        else:
            with Image.open(path) as im:
                base = im.copy()
                self._base_image = base.copy()
        # 暂时禁用水印后渲染一次作为预览底图
        s = self.settings
        original_text_enabled = s.text_enabled
        original_image_enabled = s.image_enabled
        s.text_enabled = False
        s.image_enabled = False
        try:
            out = self.renderer.render(base, s)
        finally:
            s.text_enabled = original_text_enabled
            s.image_enabled = original_image_enabled
        # 缩放到预览大小并记录缩放参数（与正常预览一致）
        label_w = self.preview_label.width()
        label_h = self.preview_label.height()
        if out.width > 0 and out.height > 0:
            pre_w, pre_h = out.width, out.height
            scale_w = label_w - 20
            scale_h = label_h - 20
            if scale_w > 50 and scale_h > 50:
                out.thumbnail((scale_w, scale_h), Image.Resampling.BILINEAR)
            self._preview_scale_x = (out.width / pre_w) if pre_w else 1.0
            self._preview_scale_y = (out.height / pre_h) if pre_h else 1.0
            self._preview_offset_x = max(0, (label_w - out.width) // 2)
            self._preview_offset_y = max(0, (label_h - out.height) // 2)
        self._drag_base_pixmap = _pil_to_qpixmap(out)
        self.preview_label.setPixmap(self._drag_base_pixmap)

    # 在预览上快速叠加水印（拖拽期间）
    def _update_overlay_preview(self):
        if not self._drag_base_pixmap:
            # 兜底：若底图未就绪则走正常预览
            self._do_update_preview()
            return
        pix = QPixmap(self._drag_base_pixmap)
        painter = QPainter(pix)
        try:
            s = self.settings
            # 绘制文本水印
            if s.text_enabled and s.text:
                # 位置转换到预览坐标
                if self.renderer.last_text_rect:
                    cw, ch = self.renderer.last_text_rect[2], self.renderer.last_text_rect[3]
                else:
                    cw, ch = 100, 40  # 兜底估计
                if s.text_custom_pos:
                    tx, ty = s.text_custom_pos
                elif self.renderer.last_text_rect:
                    tx, ty = self.renderer.last_text_rect[0], self.renderer.last_text_rect[1]
                else:
                    tx, ty = 10, 10
                px = self._preview_offset_x + round(tx * self._preview_scale_x)
                py = self._preview_offset_y + round(ty * self._preview_scale_y)
                # 字体与颜色
                font = QFont()
                # 将原始字体像素大小按预览缩放比例缩放，避免拖拽时视觉尺寸变化
                scale = max(0.1, min(self._preview_scale_x, self._preview_scale_y))
                font.setPixelSize(max(10, int(s.font_size * scale)))
                painter.setFont(font)
                color = QColor(s.color[0], s.color[1], s.color[2], s.text_alpha)
                # 描边：使用路径绘制获得更好效果
                path = QPainterPath()
                # 使用字体度量的 ascent 将基线对齐到文本矩形的顶部，避免垂直位置偏移
                fm = QFontMetrics(font)
                baseline_y = py + fm.ascent()
                path.addText(px, baseline_y, font, s.text)
                if s.stroke_enabled and s.stroke_width > 0:
                    pen = QPen(QColor(s.stroke_color[0], s.stroke_color[1], s.stroke_color[2]))
                    pen.setWidth(max(1, int(s.stroke_width * scale)))
                    painter.setPen(pen)
                    painter.drawPath(path)
                painter.fillPath(path, color)

            # 绘制图片水印
            if s.image_enabled and s.image_path:
                # 仅缓存原始 QPixmap，实际绘制时按需要尺寸缩放，避免重复缩放导致尺寸偏差
                if self._drag_img_qpixmap_cache is None:
                    try:
                        wm = QPixmap(s.image_path)
                        if not wm.isNull():
                            self._drag_img_qpixmap_cache = wm
                    except Exception:
                        self._drag_img_qpixmap_cache = None
                if self._drag_img_qpixmap_cache:
                    if self.renderer.last_image_rect:
                        iw, ih = self.renderer.last_image_rect[2], self.renderer.last_image_rect[3]
                    else:
                        iw, ih = self._drag_img_qpixmap_cache.width(), self._drag_img_qpixmap_cache.height()
                    if s.image_custom_pos:
                        ix, iy = s.image_custom_pos
                    elif self.renderer.last_image_rect:
                        ix, iy = self.renderer.last_image_rect[0], self.renderer.last_image_rect[1]
                    else:
                        ix, iy = 10, 10
                    px = self._preview_offset_x + round(ix * self._preview_scale_x)
                    py = self._preview_offset_y + round(iy * self._preview_scale_y)
                    # 叠加到预览，按预览缩放显示
                    draw_w = max(1, round(iw * self._preview_scale_x))
                    draw_h = max(1, round(ih * self._preview_scale_y))
                    painter.setOpacity(max(0.0, min(1.0, s.image_alpha / 255.0)))
                    # 根据用户的缩放百分比与渲染器计算得到的矩形宽高来绘制，确保尺寸一致
                    scaled = self._drag_img_qpixmap_cache.scaled(draw_w, draw_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
                    painter.drawPixmap(px, py, scaled)
        finally:
            painter.end()
        self.preview_label.setPixmap(pix)

    # 关闭时自动保存上次设置（单一职责：持久化当前会话）
    def closeEvent(self, e):
        try:
            self._save_last_session()
        except Exception:
            pass
        super().closeEvent(e)

    # 用户数据目录（单一职责：提供平台兼容路径）
    def _user_data_dir(self) -> str:
        base = os.environ.get("APPDATA")
        if base:
            path = os.path.join(base, "WatermarkTool")
        else:
            path = os.path.join(os.path.expanduser("~"), ".watermark_tool")
        os.makedirs(path, exist_ok=True)
        return path

    # 保存/加载上次会话（单一职责：读写 last_settings.json）
    def _save_last_session(self):
        import json
        data = {
            "settings": self._settings_to_dict(),
            "template_path": self._current_template_path,
        }
        path = os.path.join(self._user_data_dir(), "last_settings.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_last_session(self) -> bool:
        import json
        path = os.path.join(self._user_data_dir(), "last_settings.json")
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 兼容两种结构：包含 settings 键或直接是设置字典
            settings_dict = data.get("settings", data)
            self._apply_settings_dict(settings_dict)
            self._current_template_path = data.get("template_path")
            self._update_template_label()
            # 同步控件显示与使能
            self._sync_controls_from_settings()
            self._update_preview()
            return True
        except Exception:
            return False

    # 模板（单一职责：保存/加载/删除模板）
    def _update_template_label(self):
        name = os.path.basename(self._current_template_path) if getattr(self, "_current_template_path", None) else "未选择"
        self.lbl_tpl_name.setText(f"当前模板：{name}")

    def _save_template(self):
        import json
        # 通过文件管理器选择保存位置（默认用户目录）
        default_path = os.path.join(self._user_data_dir(), "watermark_template.json")
        path, _ = QFileDialog.getSaveFileName(self, "保存模板", default_path, "JSON (*.json)")
        if not path:
            return
        try:
            settings_data = self._settings_to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
            # 同步到用户目录默认模板
            user_tpl = os.path.join(self._user_data_dir(), "watermark_template.json")
            try:
                with open(user_tpl, "w", encoding="utf-8") as uf:
                    json.dump(settings_data, uf, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self._current_template_path = path
            self._update_template_label()
            QMessageBox.information(self, "提示", f"模板已保存: {path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存模板失败: {e}")

    def _load_template(self, silent: bool = False):
        import json
        if silent:
            # 启动时静默加载用户目录中的默认模板路径
            user_tpl = os.path.join(self._user_data_dir(), "watermark_template.json")
            tpl_path = user_tpl if os.path.exists(user_tpl) else (getattr(self, "_current_template_path", None) or os.path.join(os.getcwd(), "watermark_template.json"))
            if not os.path.exists(tpl_path):
                return
            try:
                with open(tpl_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._apply_settings_dict(data)
                self._current_template_path = tpl_path
                self._update_template_label()
                self._update_preview()
            except Exception:
                # 静默模式下仅忽略错误
                pass
            return
        # 非静默：通过文件管理器选择模板文件
        init_dir = getattr(self, "_current_template_path", None) or os.getcwd()
        path, _ = QFileDialog.getOpenFileName(self, "加载模板", init_dir, "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_settings_dict(data)
            # 同步到用户目录默认模板
            try:
                user_tpl = os.path.join(self._user_data_dir(), "watermark_template.json")
                with open(user_tpl, "w", encoding="utf-8") as uf:
                    json.dump(data, uf, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self._current_template_path = path
            self._update_template_label()
            QMessageBox.information(self, "提示", "模板已加载")
            self._update_preview()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载模板失败: {e}")

    def _delete_template(self):
        # 优先删除当前选择的模板文件，其次回退到默认模板路径
        path = getattr(self, "_current_template_path", None) or os.path.join(os.getcwd(), "watermark_template.json")
        try:
            if path and os.path.exists(path):
                os.remove(path)
                QMessageBox.information(self, "提示", "模板已删除")
                # 清空当前模板并更新显示
                self._current_template_path = None
                self._update_template_label()
            else:
                QMessageBox.information(self, "提示", "模板文件不存在")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除模板失败: {e}")

    def _settings_to_dict(self) -> dict:
        s = self.settings
        return {
            "text_enabled": s.text_enabled,
            "text": s.text,
            "font_size": s.font_size,
            "color": s.color,
            "text_alpha": s.text_alpha,
            "stroke_enabled": s.stroke_enabled,
            "stroke_color": s.stroke_color,
            "stroke_width": s.stroke_width,
            "image_enabled": s.image_enabled,
            "image_path": s.image_path,
            "image_scale_percent": s.image_scale_percent,
            "image_alpha": s.image_alpha,
            # 独立的文本/图片位置与自定义坐标
            "text_position": s.text_position,
            "text_custom_pos": s.text_custom_pos,
            "image_position": s.image_position,
            "image_custom_pos": s.image_custom_pos,
            "rotation_deg": s.rotation_deg,
            "output_format": s.output_format,
            "naming_rule": s.naming_rule,
            "prefix": s.prefix,
            "suffix": s.suffix,
            "jpeg_quality": s.jpeg_quality,
            "resize_percent": s.resize_percent,
        }

    def _apply_settings_dict(self, d: dict):
        s = self.settings
        s.text_enabled = d.get("text_enabled", s.text_enabled)
        s.text = d.get("text", s.text)
        s.font_size = d.get("font_size", s.font_size)
        s.color = tuple(d.get("color", list(s.color)))
        s.text_alpha = d.get("text_alpha", s.text_alpha)
        s.stroke_enabled = d.get("stroke_enabled", s.stroke_enabled)
        s.stroke_color = tuple(d.get("stroke_color", list(s.stroke_color)))
        s.stroke_width = d.get("stroke_width", s.stroke_width)
        s.image_enabled = d.get("image_enabled", s.image_enabled)
        s.image_path = d.get("image_path", s.image_path)
        s.image_scale_percent = d.get("image_scale_percent", s.image_scale_percent)
        s.image_alpha = d.get("image_alpha", s.image_alpha)
        # 兼容旧字段
        old_pos = d.get("position")
        old_custom = d.get("custom_pos")
        s.text_position = d.get("text_position", old_pos if old_pos else s.text_position)
        s.text_custom_pos = tuple(d.get("text_custom_pos")) if d.get("text_custom_pos") else (tuple(old_custom) if old_custom else s.text_custom_pos)
        s.image_position = d.get("image_position", old_pos if old_pos else s.image_position)
        s.image_custom_pos = tuple(d.get("image_custom_pos")) if d.get("image_custom_pos") else (tuple(old_custom) if old_custom else s.image_custom_pos)
        s.rotation_deg = d.get("rotation_deg", s.rotation_deg)
        s.output_format = d.get("output_format", s.output_format)
        s.naming_rule = d.get("naming_rule", s.naming_rule)
        s.prefix = d.get("prefix", s.prefix)
        s.suffix = d.get("suffix", s.suffix)
        s.jpeg_quality = d.get("jpeg_quality", s.jpeg_quality)
        s.resize_percent = d.get("resize_percent", s.resize_percent)

    # 同步控件状态到当前设置（用于加载会话/模板后）
    def _sync_controls_from_settings(self):
        s = self.settings
        # 文本水印
        self.chk_text_enable.setChecked(s.text_enabled)
        self.txt_input.setText(s.text)
        self.sp_font.setValue(s.font_size)
        self.slider_alpha.setValue(s.text_alpha)
        self.chk_stroke.setChecked(s.stroke_enabled)
        self.sp_stroke.setValue(s.stroke_width)
        self.pos_text_combo.setCurrentText(s.text_position)
        # 图片水印
        self.chk_img_enable.setChecked(s.image_enabled)
        self.sp_img_scale.setValue(s.image_scale_percent)
        self.slider_img_alpha.setValue(s.image_alpha)
        self.pos_img_combo.setCurrentText(s.image_position)
        # 导出设置
        self.cmb_format.setCurrentText(s.output_format)
        self.cmb_naming.setCurrentText(s.naming_rule)
        self.ed_prefix.setText(s.prefix)
        self.ed_suffix.setText(s.suffix)
        self.slider_quality.setValue(s.jpeg_quality)
        self.chk_resize.setChecked(s.resize_percent is not None)
        self.sp_resize.setValue(s.resize_percent or self.sp_resize.value())
        # 可见性/使能联动
        self._update_text_controls_enabled()
        self._update_img_controls_enabled()
        self._update_output_format_controls()
        self.sp_resize.setEnabled(self.chk_resize.isChecked())

    # 根据启用开关禁用/启用文本水印相关控件
    def _update_text_controls_enabled(self):
        enabled = self.chk_text_enable.isChecked()
        for w in [self.txt_input, self.sp_font, self.btn_color, self.slider_alpha, self.chk_stroke, self.sp_stroke, self.pos_text_combo, self.chk_text_drag]:
            w.setEnabled(enabled)

    # 根据启用开关禁用/启用图片水印相关控件
    def _update_img_controls_enabled(self):
        enabled = self.chk_img_enable.isChecked()
        for w in [self.btn_choose_img, self.sp_img_scale, self.slider_img_alpha, self.pos_img_combo, self.chk_img_drag_ctrl]:
            w.setEnabled(enabled)

    # 根据输出格式隐藏/显示 JPEG 质量控件
    def _update_output_format_controls(self):
        is_jpeg = (self.cmb_format.currentText() == "JPEG")
        self.lbl_quality.setVisible(is_jpeg)
        self.slider_quality.setVisible(is_jpeg)

    # 删除文本水印内容并禁用
    def _delete_text(self):
        self.settings.text = ""
        self.txt_input.setText("")
        self.settings.text_enabled = False
        self.settings.text_custom_pos = None
        self.chk_text_enable.setChecked(False)
        self._update_preview()

    # 删除图片水印并禁用
    def _delete_image(self):
        self.settings.image_path = None
        self.settings.image_enabled = False
        self.settings.image_custom_pos = None
        self.chk_img_enable.setChecked(False)
        self._update_preview()

    # 批量导出（单一职责：生成文件名与保存）
    def _export_all(self):
        if not self.image_paths:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        if not self.output_dir:
            QMessageBox.information(self, "提示", "请先选择输出目录")
            return
        # 默认禁止导出到原目录：若任何图片的父目录与输出目录相同则警告
        for p in self.image_paths:
            if os.path.dirname(p) == self.output_dir:
                QMessageBox.warning(self, "提示", "默认禁止导出到原目录，请选择不同的输出目录")
                return
        fmt = self.settings.output_format
        ok = 0
        for src in self.image_paths:
            try:
                with Image.open(src) as im:
                    out_img = self.renderer.render(im.copy(), self.settings)
                    # 输出文件名规则
                    base = os.path.basename(src)
                    name, ext = os.path.splitext(base)
                    if self.settings.naming_rule == "original":
                        out_name = name
                    elif self.settings.naming_rule == "prefix":
                        out_name = f"{self.settings.prefix}{name}"
                    else:
                        out_name = f"{name}{self.settings.suffix}"
                    # 扩展名按格式
                    out_ext = ".jpg" if fmt == "JPEG" else ".png"
                    out_path = os.path.join(self.output_dir, out_name + out_ext)
                    if fmt == "JPEG":
                        out_img = out_img.convert("RGB")
                        out_img.save(out_path, "JPEG", quality=self.settings.jpeg_quality)
                    else:
                        out_img.save(out_path, "PNG")
                    ok += 1
            except Exception as e:
                print(f"Export error for {src}: {e}")
        QMessageBox.information(self, "完成", f"成功导出 {ok} 张图片到: {self.output_dir}")


def gui_main():
    """GUI 入口函数。"""
    if not PYQT_AVAILABLE:
        print("PyQt6 未安装，请先执行: uv sync 或 pip install PyQt6")
        return
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    # 启动时优先加载上次关闭时的设置，其次回退到默认模板
    try:
        loaded = win._load_last_session()
        if not loaded:
            win._load_template(silent=True)
    except Exception:
        # 若发生异常，继续展示空白界面
        pass
    win.show()
    sys.exit(app.exec())
