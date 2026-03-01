import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_fonts():
    """注册中文字体"""
    try:
        # 尝试注册宋体
        font_path = "C:\\Windows\\Fonts\\simsun.ttc"
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\simsun.ttf"

        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("SimSun", font_path))
            return True
        else:
            # 尝试在当前目录查找
            local_font = "simsun.ttc"
            if os.path.exists(local_font):
                pdfmetrics.registerFont(TTFont("SimSun", local_font))
                return True
    except Exception as e:
        print(f"Font registration failed: {e}")
    return False


# 页面尺寸 (A4)
PAGE_WIDTH, PAGE_HEIGHT = A4

