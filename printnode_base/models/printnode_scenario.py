# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .constants import Constants


SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class PrintNodeScenario(models.Model):
    """
    Scenarios to print reports
    """
    _name = 'printnode.scenario'
    _inherit = 'printnode.logger.mixin'
    _description = 'PrintNode Scenarios'

    _rec_name = 'report_id'

    action = fields.Many2one(
        'printnode.scenario.action',
        string='Print Scenario Action',
        required=True,
        ondelete='cascade',
        help="""Choose a print action to listen""",
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help="""Activate or Deactivate the print scenario.
                If no active then move to the status \'archive\'.
                Still can by found using filters button""",
    )

    description = fields.Char(
        string='Description',
        size=200,
        help="""Text field for notes and memo.""",
    )

    domain = fields.Text(
        string='Domain',
        default='[]',
    )

    # This value used to set correct domain for scenario
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        related='action.model_id',
    )

    model = fields.Char(
        string='Related Document Model',
        related='model_id.model',
    )

    # This value used to define list of available reports
    reports_model_id = fields.Many2one(
        'ir.model',
        string='Model For Reports',
        related='action.reports_model_id',
    )

    number_of_copies = fields.Integer(string="Number of Copies", default=1)

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report',
        required=True,
        domain="[('report_type', 'in', ('qweb-pdf', 'qweb-text', 'py3o'))]",
        help="""Choose a report that will be printed""",
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

    @api.constrains('number_of_copies')
    def _check_number_of_copies(self):
        for record in self:
            if record.number_of_copies < 1:
                raise ValidationError(_("Number of Copies can't be less than 1"))

    @api.onchange('printer_id')
    def _onchange_printer(self):
        """
        Reset printer_bin field to avoid bug with printing
        in wrong bin
        """
        self.printer_bin = self.printer_id.default_printer_bin.id

    @api.onchange('action')
    def _onchange_action(self):
        """
        Reset report_id field to avoid bug with printing
        wrong reports for current scenario
        """
        self.report_id = None

    @api.onchange('active', 'action')
    def _onchange_active(self):
        actions = [
            'print_product_labels_on_transfer',
            'print_single_product_label_on_transfer',
            'print_multiple_product_labels_on_transfer',
        ]
        if not self.env.company.print_labels_format and self.active and self.action.code in actions:
            raise UserError(_(
                'To activate and use this scenario, you need to set the value '
                'of the "Default Product Labels Format" field in the settings!'
            ))

    def edit_domain(self):
        """ Returns action window with 'Domain Editor'
        """
        domain_editor = self.env.ref(
            'printnode_base.printnode_scenario_domain_editor',
            raise_if_not_found=False,
        )
        action = {
            'name': _('Domain Editor'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'printnode.scenario',
            'res_id': self.id,
            'view_id': domain_editor.id,
            'target': 'self',
        }
        return action

    def print_reports(self, action, ids_list, **kwargs):
        """
        Find all scenarios and print reports for each of them.

        Returns True when at least a single scenario found. In other cases returns False.
        """
        user = self.env.user
        company = self.env.company

        if not company.printnode_enabled:
            return False

        if not user.has_group(SECURITY_GROUP) or not user.printnode_enabled:
            # It is possible to execute scenarios from scheduled actions
            if not (self.env.context.get('printnode_from_cron', False) or company.printing_scenarios_from_crons):  # NOQA
                return False

        scenarios = self.sudo().search([
            ('active', '=', True),
            ('action.code', '=', action),
        ])

        printed = False

        for scenario in scenarios:
            objects = scenario._apply_domain(ids_list)
            scenario_method_name = f'_scenario_{scenario.action.code}'
            scenario.printnode_logger(
                Constants.SCENARIOS_LOG_TYPE,
                f"Objects to print defined: {objects._name}{objects.ids}")

            if objects:
                printer, printer_bin = scenario._get_printer()
                print_options = {'bin': printer_bin.name} if printer_bin else {}

                if scenario.model_id != scenario.reports_model_id:
                    # When we want to print reports for different model
                    # We should call a special method to print
                    scenario.printnode_logger(
                        Constants.SCENARIOS_LOG_TYPE,
                        'Model and report model do not match'
                    )
                    if hasattr(objects, scenario_method_name):
                        scenario.printnode_logger(
                            Constants.SCENARIOS_LOG_TYPE,
                            f"The {scenario_method_name} is defined for "
                            f"{objects._name} model"
                        )
                        scenario_method = getattr(objects, scenario_method_name)
                        printed = scenario_method(
                            scenario=scenario,
                            report_id=scenario.report_id,
                            printer_id=printer,
                            number_of_copies=scenario.number_of_copies,
                            options=print_options,
                            **kwargs)
                else:
                    # When model and reports model are the same
                    # We call a special method to print or
                    # pass the objects to default printnode_print method
                    scenario.printnode_logger(
                        Constants.SCENARIOS_LOG_TYPE,
                        f"Model and report model are the same - {scenario.reports_model_id.model}"
                    )
                    if hasattr(self.env[scenario.model_id.model], scenario_method_name):
                        scenario.printnode_logger(
                            Constants.SCENARIOS_LOG_TYPE,
                            f"The {scenario_method_name} is defined for "
                            f"{scenario.reports_model_id.model} model"
                        )
                        scenario_method = getattr(objects, scenario_method_name)
                        printed = scenario_method(
                            scenario=scenario,
                            report_id=scenario.report_id,
                            printer_id=printer,
                            number_of_copies=scenario.number_of_copies,
                            options=print_options,
                        )
                    else:
                        scenario.printnode_logger(
                            Constants.SCENARIOS_LOG_TYPE,
                            'Printing will be done via the default printnode_print method'
                        )
                        res = printer.printnode_print(
                            scenario.report_id,
                            objects,
                            copies=scenario.number_of_copies,
                            options=print_options,
                        )

                        printed = bool(res)

                if printed:
                    scenario.printnode_logger(Constants.SCENARIOS_LOG_TYPE, 'Printing successful')

        return printed

    def _apply_domain(self, ids_list):
        """
        Get objects by IDs with applied domain
        """
        self.ensure_one()

        if self.domain == '[]':
            return self.env[self.model_id.model].browse(ids_list)
        return self.env[self.model_id.model].search(
            expression.AND([[('id', 'in', ids_list)], safe_eval(self.domain)])
        )

    def _get_printer(self):
        """
        Return printer to use for current scenario or raise exception
        when printer cannot be selected
        """
        self.ensure_one()

        user = self.env.user
        external_printer_id, external_printer_bin = user.get_report_printer(self.report_id.id)
        printer = self.printer_id or external_printer_id
        printer_bin = self.printer_bin if self.printer_id else external_printer_bin

        if not printer:
            raise UserError(_(
                'Neither on scenario level, no on user rules level, no on user level, '
                'no on company level printer is defined for report "%s". '
                'Please, define it.') % self.report_id.name
            )
        return printer, printer_bin
