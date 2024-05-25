# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import inspect
import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class PrintNodeLoggerMixin(models.AbstractModel):
    """
    Model for logging events, preparing and writing logs to the database.
    To add logging to a model, first inherit from this model: _inherit = ['printnode.logger.mixin']
    """
    _name = 'printnode.logger.mixin'
    _description = 'PrintNode logger'

    def printnode_logger(self, log_type, log_string, **kwargs):
        """
        Event logging and preparation of logs for writing to the database

        :param str log_type: required type of logs
        :param str log_string: required event string for logging
        """

        company = self.env.company
        if not company.debug_logging:
            return False

        path, line, func = self.get_stack_info()

        log_type_id = self.env['printnode.log.type'].search([
            ('active', '=', True),
            ('name', '=', log_type),
        ])

        if log_type_id not in company.log_type_ids:
            return False

        logging_object = {
            'name': f"printnode_base.{log_type_id.name}",
            'type': 'server',
            'dbname': self._cr.dbname,
            'level': 'DEBUG',
            'message': str(log_string),
            'path': path,
            'func': func,
            'line': line
        }

        self._write_logs(logging_object, self._cr.dbname)
        return True

    def _write_logs(self, logging_object, db_name):
        """
        Writing logs to the database
        Use a new cursor to avoid rollback that could be caused by an upper method
        """
        self.env['ir.logging'].flush_model()
        try:
            db_registry = registry(db_name)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env['ir.logging'].sudo().create(logging_object)
        except psycopg2.Error as err:
            _logger.error("Error writing logs to the database: %s", err)

    def get_stack_info(self):
        """ Get info for the logged string using the "inspect" module.
        """
        call_stack_info = inspect.stack()[2]
        path = call_stack_info.filename
        line = call_stack_info.lineno
        func = call_stack_info.function

        return path, line, func


class PrintNodeLogType(models.Model):
    """PrintNode logging types entity
    """
    _name = 'printnode.log.type'
    _description = 'PrintNode Log Types'

    active = fields.Boolean(
        string='Active',
        default=True
    )

    name = fields.Char(
        string='Name of log types',
        required=True,
    )

    _sql_constraints = [
        ('name', 'unique(name)', 'Log type already exists!'),
    ]
