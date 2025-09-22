import os
import argparse
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import glob


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
                            return date_obj.strftime("%Y年%m月%d日")
                        except ValueError:
                            continue
            
            # 如果没有找到EXIF日期，使用文件修改时间
            file_time = os.path.getmtime(image_path)
            date_obj = datetime.fromtimestamp(file_time)
            return date_obj.strftime("%Y年%m月%d日")
            
    except Exception as e:
        print(f"读取 {image_path} 的EXIF信息时出错: {e}")
        # 使用文件修改时间作为备选
        try:
            file_time = os.path.getmtime(image_path)
            date_obj = datetime.fromtimestamp(file_time)
            return date_obj.strftime("%Y年%m月%d日")
        except:
            return "未知日期"


def get_position_coordinates(image_size, text_size, position):
    """根据位置参数计算文本坐标"""
    img_width, img_height = image_size
    text_width, text_height = text_size
    
    if position == "左上角":
        return (10, 10)
    elif position == "右上角":
        return (img_width - text_width - 10, 10)
    elif position == "左下角":
        return (10, img_height - text_height - 10)
    elif position == "右下角":
        return (img_width - text_width - 10, img_height - text_height - 10)
    elif position == "居中":
        return ((img_width - text_width) // 2, (img_height - text_height) // 2)
    else:
        # 默认左上角
        return (10, 10)


def add_watermark(image_path, output_path, watermark_text, font_size=24, color="white", position="右下角"):
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
            print(f"已保存水印图片: {output_path}")
            
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")


def process_images(input_path, font_size=24, color="white", position="右下角"):
    """处理指定路径下的所有图片"""
    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"错误: 路径 {input_path} 不存在")
        return
    
    # 支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
    
    # 查找所有图片文件
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_path, ext)))
        image_files.extend(glob.glob(os.path.join(input_path, ext.upper())))
    
    if not image_files:
        print(f"在 {input_path} 中没有找到图片文件")
        return
    
    # 创建输出目录
    base_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
    dir_name = os.path.basename(base_dir)
    output_dir = os.path.join(base_dir, f"{dir_name}_watermark")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 处理每张图片
    for image_file in image_files:
        # 获取EXIF日期作为水印文本
        watermark_text = get_exif_date(image_file)
        
        # 生成输出文件名
        filename = os.path.basename(image_file)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_watermark.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"处理图片: {filename} -> 水印: {watermark_text}")
        add_watermark(image_file, output_path, watermark_text, font_size, color, position)


def main():
    parser = argparse.ArgumentParser(description="图片水印添加工具")
    parser.add_argument("path", help="图片文件路径或包含图片的目录路径")
    parser.add_argument("-s", "--size", type=int, default=24, help="字体大小 (默认: 24)")
    parser.add_argument("-c", "--color", default="white", help="水印颜色 (默认: white)")
    parser.add_argument("-p", "--position", 
                       choices=["左上角", "右上角", "左下角", "右下角", "居中"],
                       default="右下角", 
                       help="水印位置 (默认: 右下角)")
    
    args = parser.parse_args()
    
    print("=== 图片水印添加工具 ===")
    print(f"输入路径: {args.path}")
    print(f"字体大小: {args.size}")
    print(f"水印颜色: {args.color}")
    print(f"水印位置: {args.position}")
    print("-" * 30)
    
    process_images(args.path, args.size, args.color, args.position)
    
    print("处理完成!")


if __name__ == "__main__":
    main()
