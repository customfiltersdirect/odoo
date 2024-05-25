# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import functools

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.http import request
from werkzeug.exceptions import BadRequest


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
