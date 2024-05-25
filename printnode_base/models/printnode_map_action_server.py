# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, exceptions, _
from ..wizard.printnode_print_reports_universal_wizard import REPORT_DOMAIN


WIZARD_TYPES = [
    ('attachments', _('Print Attachments Wizard')),
    ('reports', _('Print Reports Wizard')),
]

ACTION_NAMES = {
    'attachments': _('Print Attachments'),
    'reports': _('Print Reports'),
}

ACTION_TYPES = {
    'attachments': 'action = record.run_printnode_universal_wizard()',
    'reports': 'action = record.run_printnode_print_reports_universal_wizard()',
}


class PrintnodeMapActionServer(models.Model):
    _name = 'printnode.map.action.server'
    _description = 'Proxy model for ir.actions.server'

    active = fields.Boolean(
        string='Active',
        default=True,
    )
    name = fields.Char(
        string='Action Name',
        required=True,
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        ondelete='cascade',
        required=True,
        domain=[('transient', '=', False)],
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Model Name',
        readonly=True,
    )
    action_server_id = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Action',
        ondelete='cascade',
    )
    print_wizard_type = fields.Selection(
        selection=WIZARD_TYPES,
        string='Print Wizard Type',
        required=True,
        default='attachments',
    )

    @api.constrains('model_id', 'print_wizard_type')
    def _check_uniqueness_of_models_of_wizards(self):
        actions = self.env['printnode.map.action.server'].with_context(active_test=False).search([])
        pairs = [(a.model_id.model, a.print_wizard_type) for a in actions]

        for record in self:
            pair = (record.model_id.model, record.print_wizard_type)

            if pairs.count(pair) > 1:
                raise exceptions.ValidationError(
                    _("This type of wizard already exists for the '{}' model!").format(
                        record.model_id.name
                    )
                )

    @api.onchange('print_wizard_type')
    def onchange_name(self):
        self.name = ACTION_NAMES.get(self.print_wizard_type)

    @api.onchange('print_wizard_type', 'model_id')
    def _check_model_name(self):
        if self.print_wizard_type == 'reports' and self.model_id:
            model_reports = self.env['ir.actions.report'].search([
                *REPORT_DOMAIN,
                ('model', '=', self.model_id.model),
            ])
            if not model_reports:
                raise exceptions.ValidationError(
                    _("No reports found for this model!")
                )

    @api.model_create_multi
    def create(self, vals):
        rec = super(PrintnodeMapActionServer, self).create(vals)

        if not rec:
            return rec

        action_server = self.env['ir.actions.server'].sudo().create({
            'state': 'code',
            'name': rec.name,
            'binding_type': 'action',
            'model_id': rec.model_id.id,
            'binding_model_id': rec.model_id.id,
            'code': self._get_action_code(rec.print_wizard_type),
        })

        # Attach ir.model.data record to new action
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': f'printnode_base.printnode_ir_actions_server_{action_server.id}',
            'record': action_server,
            # Make it no updatable to avoid deletion on module upgrade
            'noupdate': True,
        }])

        rec.write({'action_server_id': action_server.id})

        return rec

    def write(self, vals):
        res = super(PrintnodeMapActionServer, self).write(vals)
        for rec in self:
            rec.action_server_id.sudo().write({
                'name': rec.name,
                'binding_model_id': rec.active and rec.model_id.id,
            })
        return res

    def unlink(self):
        action_servers = self.mapped('action_server_id')

        action_servers.sudo().unlink()

        res = super(PrintnodeMapActionServer, self).unlink()

        return res

    @staticmethod
    def _get_action_code(wizard_type):
        return ACTION_TYPES[wizard_type]
