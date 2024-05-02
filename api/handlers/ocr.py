"""
Main handler for the OCR feature
"""

import binascii
import base64
from io import BytesIO

import pytesseract

from PIL import Image

from pydantic import BaseModel
from pydantic import ValidationError

from aiohttp import web

from api.handlers.base import get_400_response
from api.handlers.base import get_422_response


class Params(BaseModel):
    image: str
    config: str = ''
    resize: int = 2
    resample: int = 1


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
        im = im.resize((im.width * params.resize, im.height *
                       params.resize), resample=params.resample)

    if params.config:
        output = pytesseract.image_to_string(im, config=params.config)
    else:
        output = pytesseract.image_to_string(im)

    return web.json_response({'message': 'All OK',
                              'data': {
                                  'output': output,
                              },
                              'status': 'success'}, status=200)
