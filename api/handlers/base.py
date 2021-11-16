"""
Base handlers and utilities
"""

from aiohttp import web


def get_400_response():
    '''Default 400 response'''
    return web.json_response({'message': 'Bad Request',
                              'data': {},
                              'status': 'unknown'}, status=400)


def get_404_response():
    '''Default 404 response'''
    return web.json_response({'message': 'Not found',
                              'data': {},
                              'status': 'unknown'}, status=404)


def get_422_response(details):
    '''Default validation error response'''
    return web.json_response({'message': 'Validation Errors',
                              'data': {'details': details},
                              'status': 'error'}, status=422)
