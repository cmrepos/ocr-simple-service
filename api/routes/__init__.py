"""
API: init routes
"""

from api.routes.ocr import init_ocr_routes


def init_routes(app):
    '''Init some routes for the App'''
    init_ocr_routes(app)
