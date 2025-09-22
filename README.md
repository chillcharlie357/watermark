# Image Watermark Tool

A Python command-line tool that adds watermarks to images based on EXIF shooting date.

## Features

- 📸 Automatically reads shooting time from image EXIF data
- 🎨 Supports custom font size, color, and watermark position
- 📁 Batch processes all images in a directory
- 💾 Automatically creates watermarked images and saves them to specified directory

## Installation

Install dependencies using uv package manager:

```bash
uv sync
```

## Usage

### Basic Usage

```bash
uv run python main.py <image_path_or_directory>
```

### Advanced Options

```bash
uv run python main.py <path> -s <font_size> -c <color> -p <position>
```

### Parameters

- `path`: Image file path or directory path containing images (required)
- `-s, --size`: Font size (default: 24)
- `-c, --color`: Watermark color (default: white)
- `-p, --position`: Watermark position, options:
  - top-left
  - top-right
  - bottom-left
  - bottom-right (default)
  - center

### Examples

1. **Process a single image file**:
   ```bash
   uv run python main.py photo.jpg
   ```

2. **Process entire directory**:
   ```bash
   uv run python main.py /path/to/photos/
   ```

3. **Custom watermark style**:
   ```bash
   uv run python main.py photos/ -s 32 -c red -p top-left
   ```

4. **Large font watermark in center**:
   ```bash
   uv run python main.py photos/ -s 48 -c yellow -p center
   ```

## Output

- The program creates a new directory named `original_directory_name_watermark` under the original directory
- Processed images are saved in JPEG format with `_watermark.jpg` suffix
- Watermark text format: `Month DD, YYYY` (e.g., "January 15, 2024")

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

## Notes

- If images don't have EXIF data, the program uses file modification time as watermark
- The program automatically handles image format conversion to ensure JPEG output
- Font support requires appropriate font files to be installed on the system
