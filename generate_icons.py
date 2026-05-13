from PIL import Image, ImageDraw
import os

def create_placeholder(filename, color):
    # 创建 64x64 的透明背景图像
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的矩形/圆形作为占位
    # 颜色格式: (R, G, B, A)
    draw.ellipse([10, 10, 54, 54], fill=color)
    
    output_path = f"gaokao-miniprogram/src/static/tabbar/{filename}"
    img.save(output_path)
    print(f"Generated: {output_path}")

# 定义颜色
GREY = (156, 163, 175, 255) # #9CA3AF
ORANGE = (249, 115, 22, 255) # #F97316

# 确保目录存在
os.makedirs("gaokao-miniprogram/src/static/tabbar", exist_ok=True)

# 生成图标
create_placeholder("home.png", GREY)
create_placeholder("home-active.png", ORANGE)
create_placeholder("assess.png", GREY)
create_placeholder("assess-active.png", ORANGE)
create_placeholder("profile.png", GREY)
create_placeholder("profile-active.png", ORANGE)
