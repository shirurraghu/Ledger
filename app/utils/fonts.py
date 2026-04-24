import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

def register_fonts():
    font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts'))
    fonts = {
        "NotoSans": {
            "normal": "NotoSans-Regular.ttf",
            "bold": "NotoSans-Bold.ttf",
            "italic": "NotoSans-Italic.ttf",
            "bold_italic": "NotoSans-BoldItalic.ttf",
        },
        "NotoSansDevanagari": {
            "normal": "NotoSansDevanagari.ttf",
        },
        "NotoSansKannada": {
            "normal": "NotoSansKannada.ttf",
        },
        "NotoSansTamil": {
            "normal": "NotoSansTamil.ttf",
        },
        "NotoSansTelugu": {
            "normal": "NotoSansTelugu.ttf",
        },
        "NotoSansMalayalam": {
            "normal": "NotoSansMalayalam.ttf",
        },
        "NotoSansBengali": {
            "normal": "NotoSansBengali.ttf",
        }
    }

    for name, paths in fonts.items():
        if "normal" in paths:
            pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, paths['normal'])))
        if "bold" in paths:
            pdfmetrics.registerFont(TTFont(f"{name}-Bold", os.path.join(font_dir, paths['bold'])))
        if "italic" in paths:
            pdfmetrics.registerFont(TTFont(f"{name}-Italic", os.path.join(font_dir, paths['italic'])))
        if "bold_italic" in paths:
            pdfmetrics.registerFont(TTFont(f"{name}-BoldItalic", os.path.join(font_dir, paths['bold_italic'])))

        if all(k in paths for k in ("normal", "bold", "italic", "bold_italic")):
            registerFontFamily(name, normal=name, bold=f"{name}-Bold", italic=f"{name}-Italic", boldItalic=f"{name}-BoldItalic")
