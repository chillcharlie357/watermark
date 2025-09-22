# 图片水印添加工具

一个使用Python开发的命令行工具，可以为图片添加基于EXIF拍摄日期的水印。

## 功能特性

- 📸 自动读取图片的EXIF信息中的拍摄时间
- 🎨 支持自定义字体大小、颜色和水印位置
- 📁 批量处理目录中的所有图片
- 💾 自动创建带水印的新图片并保存到指定目录

## 安装依赖

使用uv包管理器安装依赖：

```bash
uv sync
```

## 使用方法

### 基本用法

```bash
python main.py <图片路径或目录路径>
```

### 高级选项

```bash
python main.py <路径> -s <字体大小> -c <颜色> -p <位置>
```

### 参数说明

- `path`: 图片文件路径或包含图片的目录路径（必需）
- `-s, --size`: 字体大小，默认为24
- `-c, --color`: 水印颜色，默认为white
- `-p, --position`: 水印位置，可选值：
  - 左上角
  - 右上角
  - 左下角
  - 右下角（默认）
  - 居中

### 使用示例

1. **处理单个图片文件**：
   ```bash
   python main.py photo.jpg
   ```

2. **处理整个目录**：
   ```bash
   python main.py /path/to/photos/
   ```

3. **自定义水印样式**：
   ```bash
   python main.py photos/ -s 32 -c red -p 左上角
   ```

4. **居中位置的大字体水印**：
   ```bash
   python main.py photos/ -s 48 -c yellow -p 居中
   ```

## 输出说明

- 程序会在原目录下创建一个名为 `原目录名_watermark` 的新目录
- 处理后的图片会保存为JPEG格式，文件名后缀为 `_watermark.jpg`
- 水印文本格式为：`YYYY年MM月DD日`

## 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

## 注意事项

- 如果图片没有EXIF信息，程序会使用文件的修改时间作为水印
- 程序会自动处理图片格式转换，确保输出为JPEG格式
- 中文字体支持需要系统安装相应的字体文件
