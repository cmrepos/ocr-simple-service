"""
Main handler for the OCR feature
"""

import os

import binascii
import base64
from io import BytesIO

import subprocess
from tempfile import NamedTemporaryFile

import pytesseract

import cv2
import numpy as np

from PIL import Image, ImageOps

from pydantic import BaseModel
from pydantic import ValidationError

from aiohttp import web

from api.handlers.base import get_400_response
from api.handlers.base import get_422_response


class Params(BaseModel):
    image: str
    config: str = '--oem 3 --psm 6'
    resize: float = 1.0
    resample: int = 1
    native: bool = True
    improve: bool = True
    invert: bool = False


def run_tesseract(image, config, output):
    if config:
        config = config.split()
    command = ['tesseract']
    command.extend(config)
    command.extend([image, output])
    subprocess.call(command)


def improve_image(img):
    # DPI of less than 300 dpi
    img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    # image to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Applying dilation and erosion to remove the noise
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    # Blur
    # cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    _, img = cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # cv2.threshold(cv2.medianBlur(img, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # cv2.adaptiveThreshold(cv2.GaussianBlur(img, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    # cv2.adaptiveThreshold(cv2.bilateralFilter(img, 9, 75, 75), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    # cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    return img


async def image_to_string(request):
    params = await request.json()
    if not params:
        return get_400_response()

    try:
        params = Params(**params)
    except ValidationError as v_errors:
        return get_422_response(v_errors.errors())

    try:
        image = BytesIO(base64.decodebytes(
                        params.image.encode('utf8')))
    except (TypeError, binascii.Error):
        return web.json_response({'message': 'It is not a valid image',
                                  'data': {},
                                  'status': 'error'}, status=400)

    im = Image.open(image)

    if params.resize:
        im = im.resize((int(im.width * params.resize), int(im.height *
                       params.resize)), resample=params.resample)

    if params.invert:
        im = im.convert('RGB')
        im = ImageOps.invert(im)

    if params.improve:
        open_cv_img = improve_image(np.array(im))
        im = Image.fromarray(open_cv_img)

    if not params.native:
        if params.config:
            output = pytesseract.image_to_string(im, config=params.config)
        else:
            output = pytesseract.image_to_string(im)
    else:
        with NamedTemporaryFile(delete=False, suffix='.png') as image_f:
            im.save(image_f, format='PNG')
            output_f = NamedTemporaryFile(delete=False)
            output_f.close()
            run_tesseract(image_f.name, params.config, output_f.name)
            with open(output_f.name + '.txt', 'r', encoding='utf8') as f:
                output = f.read()
            os.remove(output_f.name + '.txt')

    im.close()

    return web.json_response({'message': 'All OK',
                              'data': {'output': output},
                              'status': 'success'}, status=200)
