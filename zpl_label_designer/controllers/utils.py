import functools

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.http import request, db_filter
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized


def add_env(func):
    """
    Add environment to the request
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        db = kwargs.get('db')
        if not db:
            raise BadRequest("Database name is required")

        registry = Registry(db).check_signaling()
        with registry.cursor() as cr:
            request.env = api.Environment(cr, SUPERUSER_ID, {})
            return func(*args, **kwargs)
    return wrapper


def validate(func):
    """
    Does a basic validation of request. Validates:
    - API Keys
    - Database
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Validate database
        db = kwargs.get('db')
        if not db:
            raise BadRequest("Database name is required")

        if not db_filter([db]):
            raise NotFound('Database not found')

        request.session.db = db
        env = request.env(user=SUPERUSER_ID)

        # Validate API Key
        if not hasattr(env['res.config.settings'], 'get_zld_api_key'):
            # Most likely that no module installed
            raise NotFound('ZPL Label Designer module is not installed or need to be upgraded')

        key_from_odoo = env['res.config.settings'].get_zld_api_key()
        key_from_request = request.httprequest.headers.get('ZLD-API-KEY')

        if key_from_odoo != key_from_request:
            raise Unauthorized('Invalid API key')

        return func(*args, **kwargs)
    return wrapper


def required(*arguments):
    """
    Checks required parameters in request data
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if request.httprequest.method == 'GET':
                data = request.args
            else:
                data = request.get_json_data()

            for arg in arguments:
                if arg not in data:
                    raise BadRequest(f"Required parameters missed: {arg}")

            return func(*args, **kwargs)
        return wrapper
    return decorator
