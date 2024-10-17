# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .constants import Constants


class PrintNodeActionButton(models.Model):
    """ Call Button
    """
    _name = 'printnode.action.button'
    _inherit = 'printnode.logger.mixin'
    _description = 'PrintNode Action Button'

    _rec_name = 'report_id'

    active = fields.Boolean(
        string='Active',
        default=True,
        help="""Activate or Deactivate the print action button.
                If no active then move to the status \'archive\'.
                Still can by found using filters button""",
    )

    description = fields.Char(
        string='Description',
        size=64,
        help="""Text field for notes and memo.""",
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )

    model = fields.Char(
        string='Related Document Model',
        related='model_id.model',
        help="""Choose a model where the button is placed. You can find the
                model name in the URL. For example the model of this page is
                \'model=printnode.action.button\'.
                Check this in the URL after the \'model=\'.""",
    )

    method = fields.Char(
        string='Method Name',
        size=64,
    )

    method_id = fields.Many2one(
        'printnode.action.method',
        string='Method ID',
        required=True,
        ondelete='cascade',
        help="""The technical name of the action that a button performs.
                It can be seen only in debug mode. Hover the cursor on
                the desired button using debug mode and type a method name
                in this field.""",
    )

    number_of_copies = fields.Integer(string="Number of Copies", default=1)

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report',
        required=True,
        domain="[('report_type', 'in', ('qweb-pdf', 'qweb-text', 'py3o'))]",
        help="""Choose a report that will be printed after you hit a button""",
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        required=False,
        domain='[("printer_id", "=", printer_id)]',
    )

    preprint = fields.Boolean(
        'Print before action',
        help="""By default the report will be printed after your action.
                First you click a button, server make the action then print
                result of this. If you want to print first and only after
                that make an action assigned to the button, then activate
                this field. Valid per each action (button).""",
    )

    domain = fields.Text(
        string='Domain',
        default='[]',
    )

    @api.onchange('printer_id')
    def _onchange_printer(self):
        """
        Reset printer_bin field to avoid bug with printing
        in wrong bin
        """
        self.printer_bin = self.printer_id.default_printer_bin.id

    @api.constrains('number_of_copies')
    def _check_number_of_copies(self):
        for record in self:
            if record.number_of_copies < 1:
                raise ValidationError(_("Number of Copies can't be less than 1"))

    def _get_model_objects(self, ids_list):
        self.ensure_one()
        related_model = self.env[self.model]
        if not ids_list:
            return related_model
        if self.domain == '[]':
            return related_model.browse(ids_list)
        return related_model.search(
            expression.AND([
                [
                    ('id', 'in', ids_list),
                    # TODO: Perhaps we need to add this ('printnode_printed', '=', False),
                ],
                safe_eval(self.domain),
            ])
        )

    def _get_action_printer(self):
        self.ensure_one()

        user = self.env.user
        external_printer_id, external_printer_bin = user.get_report_printer(self.report_id.id)
        printer = self.printer_id or external_printer_id
        printer_bin = self.printer_bin if self.printer_id else external_printer_bin

        if not printer:
            raise UserError(_(
                'Neither on action button level, no on user rules level, no on user level, '
                'no on company level printer is defined for method "%s". '
                'Please, define it.', self.method_id.name
            ))
        return printer, printer_bin

    def edit_domain(self):
        """ Returns action window with 'Domain Editor'
        """
        domain_editor = self.env.ref(
            'printnode_base.printnode_domain_editor',
            raise_if_not_found=False,
        )
        action = {
            'name': _('Domain Editor'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'printnode.action.button',
            'res_id': self.id,
            'view_id': domain_editor.id,
            'target': 'self',
        }
        return action

    def _get_post_pre_action_button_ids(self, model, method):
        """ Returns action button ids (pre_ & post_)
        """
        actions = self.env[self._name].sudo().search([
            ('model_id.model', '=', model),
            ('method_id.method', '=', method),
            ('report_id', '!=', False),
        ])
        post_ids, pre_ids = [], []

        for action in actions:
            if action.preprint:
                pre_ids.append(action.id)
                action.printnode_logger(
                    Constants.ACTION_BUTTONS_LOG_TYPE,
                    f"Printing will occur before the {action} action is executed")
            else:
                post_ids.append(action.id)

        return post_ids, pre_ids

    def print_reports(self, action_object_ids):
        """ Print reports for action buttons
        """
        for action in self:
            action.printnode_logger(Constants.ACTION_BUTTONS_LOG_TYPE, f'Action button: {action}')
            objects = action._get_model_objects(action_object_ids)
            if not objects:
                continue

            action.printnode_logger(
                Constants.ACTION_BUTTONS_LOG_TYPE,
                f'Model objects to printing: {objects}')

            printer, printer_bin = action._get_action_printer()
            action.printnode_logger(Constants.ACTION_BUTTONS_LOG_TYPE,
                                    f'Printer defined: {printer}')

            options = {'bin': printer_bin.name} if printer_bin else {}
            printer.printnode_print(
                action.report_id,
                objects,
                copies=action.number_of_copies,
                options=options,
            )
