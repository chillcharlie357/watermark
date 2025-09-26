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
    from PyQt6.QtGui import QImage, QPixmap, QIcon
    from PyQt6.QtCore import QSize, QPoint, Qt
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
    position: str = "bottom-right"  # 九宫格：top-left/top-center/top-right/center-left/center/center-right/bottom-left/bottom-center/bottom-right
    custom_pos: Optional[Tuple[int, int]] = None  # 手动拖拽坐标（左上角）
    rotation_deg: float = 0.0  # 可选

    # 导出
    output_format: str = "JPEG"  # JPEG 或 PNG
    naming_rule: str = "suffix"  # original/prefix/suffix
    prefix: str = "wm_"
    suffix: str = "_watermarked"
    jpeg_quality: int = 90  # 0-100
    resize_percent: Optional[int] = None  # 按百分比缩放原图（可选）


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    """PIL.Image 转为 QPixmap 用于预览。"""
    if img.mode != "RGB":
        img = img.convert("RGB")
    data = img.tobytes("raw", "RGB")
    qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
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

        # 绘制文本水印
        if settings.text_enabled and settings.text:
            self._draw_text(draw, image, settings)

        # 绘制图片水印
        if settings.image_enabled and settings.image_path and os.path.exists(settings.image_path):
            self._draw_image(image, settings)

        # 旋转（整体渲染后再旋转）可选：此处为简单实现，避免锯齿可考虑更复杂算法
        if settings.rotation_deg and abs(settings.rotation_deg) > 0.01:
            image = image.rotate(settings.rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)

        return image

    def _get_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", font_size)
            except:
                return ImageFont.load_default()

    def _resolve_position(self, image: Image.Image, content_size: Tuple[int, int], settings: WatermarkSettings) -> Tuple[int, int]:
        if settings.custom_pos is not None:
            x = max(0, min(image.width - content_size[0], settings.custom_pos[0]))
            y = max(0, min(image.height - content_size[1], settings.custom_pos[1]))
            return (x, y)
        return _compute_nine_grid_position((image.width, image.height), content_size, settings.position)

    def _draw_text(self, draw: ImageDraw.ImageDraw, image: Image.Image, settings: WatermarkSettings) -> None:
        font = self._get_font(settings.font_size)
        # 文本尺寸
        bbox = draw.textbbox((0, 0), settings.text, font=font, stroke_width=settings.stroke_width if settings.stroke_enabled else 0)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x, y = self._resolve_position(image, (text_w, text_h), settings)
        # 颜色+透明度
        r, g, b = settings.color
        fill = (r, g, b, settings.text_alpha)
        # 创建透明层，避免直接在背景上叠加无法控制 alpha
        txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        txt_draw = ImageDraw.Draw(txt_layer)
        # 描边支持
        stroke_w = settings.stroke_width if settings.stroke_enabled else 0
        stroke_fill = (*settings.stroke_color, settings.text_alpha) if settings.stroke_enabled else None
        txt_draw.text((x, y), settings.text, fill=fill, font=font, stroke_width=stroke_w, stroke_fill=stroke_fill)
        image.paste(txt_layer, (0, 0), txt_layer)

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
            # 位置
            x, y = self._resolve_position(image, (wm.width, wm.height), settings)
            # 叠加
            image.paste(wm, (x, y), wm)
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

        # 位置九宫格
        pos_box = QHBoxLayout()
        self.pos_combo = QComboBox()
        self.pos_combo.addItems([
            "top-left","top-center","top-right",
            "center-left","center","center-right",
            "bottom-left","bottom-center","bottom-right"
        ])
        self.pos_combo.setCurrentText(self.settings.position)
        self.pos_combo.currentTextChanged.connect(self._on_position_changed)
        self.chk_drag = QCheckBox("启用拖拽定位")
        self.chk_drag.setChecked(False)
        pos_box.addWidget(QLabel("预设位置"))
        pos_box.addWidget(self.pos_combo)
        pos_box.addWidget(self.chk_drag)
        center_box.addLayout(pos_box)

        layout.addLayout(center_box, 7)

        # 右侧：控制面板
        right_box = QVBoxLayout()

        # 文本水印设置
        grp_text = QGroupBox("文本水印")
        vb_text = QVBoxLayout(grp_text)
        self.chk_text_enable = QCheckBox("启用文本水印")
        self.chk_text_enable.setChecked(self.settings.text_enabled)
        self.chk_text_enable.stateChanged.connect(lambda _: self._update_preview())
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
        self.chk_img_enable.stateChanged.connect(lambda _: self._update_preview())
        self.btn_choose_img = QPushButton("选择 PNG")
        self.btn_choose_img.clicked.connect(self._choose_image)
        self.sp_img_scale = QSpinBox(); self.sp_img_scale.setRange(1, 500); self.sp_img_scale.setValue(self.settings.image_scale_percent)
        self.sp_img_scale.valueChanged.connect(self._on_img_scale_changed)
        self.slider_img_alpha = QSlider(Qt.Orientation.Horizontal); self.slider_img_alpha.setRange(0, 255); self.slider_img_alpha.setValue(self.settings.image_alpha)
        self.slider_img_alpha.valueChanged.connect(self._on_img_alpha_changed)
        vb_img.addWidget(self.chk_img_enable)
        vb_img.addWidget(self.btn_choose_img)
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
        vb_out.addWidget(self.btn_choose_out)
        vb_out.addWidget(QLabel("输出格式")); vb_out.addWidget(self.cmb_format)
        vb_out.addWidget(QLabel("命名规则")); vb_out.addWidget(self.cmb_naming)
        vb_out.addWidget(QLabel("前缀")); vb_out.addWidget(self.ed_prefix)
        vb_out.addWidget(QLabel("后缀")); vb_out.addWidget(self.ed_suffix)
        vb_out.addWidget(QLabel("JPEG质量")); vb_out.addWidget(self.slider_quality)
        vb_out.addWidget(self.chk_resize); vb_out.addWidget(QLabel("缩放(%)")); vb_out.addWidget(self.sp_resize)
        right_box.addWidget(grp_out)

        # 模板管理
        grp_tpl = QGroupBox("模板与设置")
        vb_tpl = QVBoxLayout(grp_tpl)
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
        self._update_preview()

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

    # 预览更新（单一职责：渲染当前图片与设置）
    def _update_preview(self):
        if self.current_index < 0 or self.current_index >= len(self.image_paths):
            return
        path = self.image_paths[self.current_index]
        try:
            with Image.open(path) as im:
                out = self.renderer.render(im.copy(), self.settings)
                # 为避免预览过大，缩放到窗口大小
                label_w = self.preview_label.width()
                label_h = self.preview_label.height()
                if out.width > 0 and out.height > 0:
                    scale_w = label_w - 20
                    scale_h = label_h - 20
                    if scale_w > 50 and scale_h > 50:
                        out.thumbnail((scale_w, scale_h), Image.Resampling.LANCZOS)
                self.preview_label.setPixmap(_pil_to_qpixmap(out))
        except Exception as e:
            print(f"Preview error: {e}")

    # 预设位置变更
    def _on_position_changed(self, v: str):
        self.settings.position = v
        self.settings.custom_pos = None
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

    # 图片水印设置回调
    def _choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "PNG Images (*.png)")
        if path:
            self.settings.image_path = path
            self.settings.image_enabled = True
            self.chk_img_enable.setChecked(True)
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
        self._update_preview()

    # 预览区拖拽定位（单一职责：处理手动拖拽）
    def mousePressEvent(self, e):
        if self.chk_drag.isChecked() and e.button() == Qt.MouseButton.LeftButton and self.preview_label.underMouse():
            self._dragging = True
            self._drag_offset = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self._dragging and self.current_index >= 0:
            # 将鼠标坐标映射到原图坐标（近似，基于缩放后的预览尺寸）
            pos = e.position().toPoint()
            dx = pos.x() - self._drag_offset.x()
            dy = pos.y() - self._drag_offset.y()
            # 简化实现：直接使用预览坐标作为自定义位置
            self.settings.custom_pos = (max(0, dx), max(0, dy))
            self._update_preview()

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    # 模板（单一职责：保存/加载设置）
    def _save_template(self):
        import json
        tpl_path = os.path.join(os.getcwd(), "watermark_template.json")
        try:
            with open(tpl_path, "w", encoding="utf-8") as f:
                json.dump(self._settings_to_dict(), f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "提示", f"模板已保存: {tpl_path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存模板失败: {e}")

    def _load_template(self, silent: bool = False):
        import json
        tpl_path = os.path.join(os.getcwd(), "watermark_template.json")
        if not os.path.exists(tpl_path):
            if not silent:
                QMessageBox.information(self, "提示", "未找到模板文件")
            return
        try:
            with open(tpl_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_settings_dict(data)
            if not silent:
                QMessageBox.information(self, "提示", "模板已加载")
            self._update_preview()
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "错误", f"加载模板失败: {e}")

    def _delete_template(self):
        tpl_path = os.path.join(os.getcwd(), "watermark_template.json")
        try:
            if os.path.exists(tpl_path):
                os.remove(tpl_path)
                QMessageBox.information(self, "提示", "模板已删除")
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
            "position": s.position,
            "custom_pos": s.custom_pos,
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
        s.position = d.get("position", s.position)
        s.custom_pos = tuple(d.get("custom_pos")) if d.get("custom_pos") else None
        s.rotation_deg = d.get("rotation_deg", s.rotation_deg)
        s.output_format = d.get("output_format", s.output_format)
        s.naming_rule = d.get("naming_rule", s.naming_rule)
        s.prefix = d.get("prefix", s.prefix)
        s.suffix = d.get("suffix", s.suffix)
        s.jpeg_quality = d.get("jpeg_quality", s.jpeg_quality)
        s.resize_percent = d.get("resize_percent", s.resize_percent)

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
    # 尝试自动加载上次模板（静默模式）
    try:
        win._load_template(silent=True)
    except Exception:
        pass
    win.show()
    sys.exit(app.exec())
