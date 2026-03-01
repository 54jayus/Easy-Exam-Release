import os
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

def register_fonts():
    """注册中文字体"""
    try:
        registered_any = False
        registered_names = set(pdfmetrics.getRegisteredFontNames())

        def _try_register_ttf(name: str, path: str) -> bool:
            if name in registered_names:
                return True
            if not os.path.exists(path):
                return False
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered_names.add(name)
                return True
            except Exception:
                return False

        def _try_register_ttc(name: str, path: str, subfont_index: int) -> bool:
            if name in registered_names:
                return True
            if not os.path.exists(path):
                return False
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont_index))
                registered_names.add(name)
                return True
            except Exception:
                return False

        simsun_ttf_paths = ["C:\\Windows\\Fonts\\simsun.ttf", "simsun.ttf"]
        simsun_ttc_paths = ["C:\\Windows\\Fonts\\simsun.ttc", "simsun.ttc"]
        simsunb_ttf_paths = ["C:\\Windows\\Fonts\\simsunb.ttf", "simsunb.ttf"]

        for p in simsun_ttf_paths:
            if _try_register_ttf("SimSun", p):
                registered_any = True
                break

        if "SimSun" not in registered_names:
            for p in simsun_ttc_paths:
                if _try_register_ttc("SimSun", p, subfont_index=0):
                    registered_any = True
                    break

        for p in simsunb_ttf_paths:
            if _try_register_ttf("SimSun-Bold", p):
                registered_any = True
                break

        if "STSong-Light" not in registered_names:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
                registered_any = True
            except Exception:
                pass

        if registered_any:
            return True
    except Exception as e:
        logger.warning("Font registration failed: %s", e)
    return False


# 页面尺寸 (A4)
PAGE_WIDTH, PAGE_HEIGHT = A4
