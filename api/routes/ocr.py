"""
OCR service routes
"""

from api.handlers.ocr import image_to_string


def init_ocr_routes(app):
    app.router.add_route('POST', r'/imagetostring', image_to_string)
